import os
import base64
import uuid
from datetime import datetime
from database import get_db_connection
from crypto.keygen import generate_document_keys, deserialize_key
from crypto.signature import sign_document_content, sha3_256_hash
from crypto.verification import verify_signed_document
from crypto.crypto_utils import decrypt_private_key
from file_selector import get_file_path

def sign_and_send_document(sender_id, sender_email, receiver_id, receiver_email, document_name, user_password, use_gui=True):
    """
    Assina e envia um documento com seleção de arquivo via interface gráfica ou terminal.
    
    Args:
        sender_id: ID do usuário remetente
        sender_email: Email do remetente
        receiver_id: ID do usuário destinatário
        receiver_email: Email do destinatário
        document_name: Nome/título do documento
        user_password: Senha do usuário para criptografar chave privada
        use_gui: Se deve usar interface gráfica para seleção de arquivo
    
    Returns:
        tuple: (sucesso, mensagem)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Seleção do arquivo
        print(f"\n=== SELECIONANDO ARQUIVO PARA ASSINAR ===")
        print(f"Título do documento: {document_name}")
        
        document_path = get_file_path(use_gui=use_gui)
        
        if not document_path:
            return False, "Seleção de arquivo cancelada."
        
        print(f"Arquivo selecionado: {document_path}")
        
        if not os.path.exists(document_path):
            return False, "Arquivo não encontrado."

        # Lê o conteúdo do arquivo
        with open(document_path, "rb") as f:
            document_content_bytes = f.read()
        
        # Verifica se o arquivo não está vazio
        if len(document_content_bytes) == 0:
            return False, "O arquivo selecionado está vazio."
        
        # Tenta decodificar como texto (para assinatura)
        try:
            document_content_text = document_content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Se não for texto UTF-8, usa o conteúdo em base64
            document_content_text = base64.b64encode(document_content_bytes).decode("utf-8")
        
        document_content_b64 = base64.b64encode(document_content_bytes).decode()

        print("Gerando chaves criptográficas...")
        
        # Gera chaves específicas para este documento
        public_key_pem, private_key_encrypted, document_id, public_key_tuple, private_key_tuple = \
            generate_document_keys(user_password)
        
        print("Assinando documento...")
        
        # Assina o documento
        signature_package = sign_document_content(
            document_content_text,  # Conteúdo como string para assinatura
            private_key_tuple, 
            sender_email, 
            receiver_email
        )
        
        print("Salvando no banco de dados...")
        
        # Salva documento no banco
        cursor.execute("""
            INSERT INTO documents (
                document_id, sender_id, receiver_id, document_name,
                document_content, document_hash, public_key,
                private_key_encrypted, signature, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            sender_id,
            receiver_id,
            document_name,
            signature_package["document_content"],  # Já está em base64
            signature_package["document_hash"],     # Já está em base64
            public_key_pem,
            private_key_encrypted,
            signature_package["signature"],
            "sent",
            datetime.now()
        ))
        
        conn.commit()
        
        # Informações do documento criado
        file_size = len(document_content_bytes)
        file_size_str = f"{file_size} bytes"
        if file_size > 1024:
            file_size_str = f"{file_size/1024:.1f} KB"
        if file_size > 1024*1024:
            file_size_str = f"{file_size/(1024*1024):.1f} MB"
        
        success_msg = f"""Documento assinado e enviado com sucesso!

Detalhes:
- ID do documento: {document_id}
- Arquivo: {os.path.basename(document_path)}
- Tamanho: {file_size_str}
- Destinatário: {receiver_email}
- Algoritmo: RSA-PSS com SHA3-256"""
        
        return True, success_msg
        
    except ValueError as e:
        conn.rollback()
        return False, f"Erro de segurança: {e}. Verifique sua senha."
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao assinar e enviar documento: {e}"
    finally:
        conn.close()

def get_sent_documents(user_id):
    """
    Obtém lista de documentos enviados pelo usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT d.document_id, d.document_name, u.nome as receiver_name,
                   u.email as receiver_email, d.status, d.created_at, d.verified_at
            FROM documents d
            JOIN users u ON d.receiver_id = u.user_id
            WHERE d.sender_id = ?
            ORDER BY d.created_at DESC
        """, (user_id,))
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "document_id": row["document_id"],
                "document_name": row["document_name"],
                "receiver_name": row["receiver_name"],
                "receiver_email": row["receiver_email"],
                "status": row["status"],
                "created_at": row["created_at"],
                "verified_at": row["verified_at"]
            })
        return documents
    finally:
        conn.close()

def get_received_documents(user_id):
    """
    Obtém lista de documentos recebidos pelo usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT d.document_id, d.document_name, u.nome as sender_name,
                   u.email as sender_email, d.status, d.created_at, d.verified_at
            FROM documents d
            JOIN users u ON d.sender_id = u.user_id
            WHERE d.receiver_id = ?
            ORDER BY d.created_at DESC
        """, (user_id,))
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "document_id": row["document_id"],
                "document_name": row["document_name"],
                "sender_name": row["sender_name"],
                "sender_email": row["sender_email"],
                "status": row["status"],
                "created_at": row["created_at"],
                "verified_at": row["verified_at"]
            })
        return documents
    finally:
        conn.close()

def get_document_details(document_id, user_id):
    """
    Obtém detalhes completos de um documento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT d.document_id, d.document_name, d.document_content, d.document_hash,
                   d.public_key, d.private_key_encrypted, d.signature, d.status,
                   d.created_at, d.verified_at,
                   s.nome as sender_name, s.email as sender_email,
                   r.nome as receiver_name, r.email as receiver_email
            FROM documents d
            JOIN users s ON d.sender_id = s.user_id
            JOIN users r ON d.receiver_id = r.user_id
            WHERE d.document_id = ? AND (d.sender_id = ? OR d.receiver_id = ?)
        """, (document_id, user_id, user_id))
        document = cursor.fetchone()
        if document:
            return dict(document)
        return None
    finally:
        conn.close()

def verify_document(document_id, verifier_id):
    """
    Verifica a autenticidade de um documento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        document = get_document_details(document_id, verifier_id)
        if not document:
            return False, "Documento não encontrado ou sem permissão."

        print("Verificando assinatura digital...")
        
        # Reconstruir o signature_package para a função verify_signed_document
        signature_package = {
            "document_content": document["document_content"],
            "document_hash": document["document_hash"],
            "signature": document["signature"],
            "sender_email": document["sender_email"],
            "receiver_email": document["receiver_email"],
            "timestamp": document["created_at"],
            "algorithm": "RSA-PSS",
            "hash_algorithm": "SHA3-256"
        }
        
        public_key_pem = document["public_key"]

        verification_result = verify_signed_document(signature_package, public_key_pem)
        
        new_status = "verified" if verification_result["valid"] else "rejected"
        verified_at = datetime.now()

        cursor.execute("UPDATE documents SET status = ?, verified_at = ? WHERE document_id = ?",
                       (new_status, verified_at, document_id))
        
        # Log da verificação
        error_message = verification_result["error"] if not verification_result["valid"] else None
        cursor.execute("""
            INSERT INTO verification_logs (document_id, verifier_id, result, error_message, verified_at)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, verifier_id, new_status, error_message, verified_at))
        
        conn.commit()
        
        if verification_result["valid"]:
            success_msg = f"""✅ DOCUMENTO VERIFICADO COM SUCESSO!

Detalhes da verificação:
- Documento: {document['document_name']}
- Remetente: {document['sender_name']} ({document['sender_email']})
- Data de envio: {document['created_at']}
- Algoritmo: RSA-PSS com SHA3-256
- Status: ASSINATURA VÁLIDA

A integridade e autenticidade do documento foram confirmadas."""
            return True, success_msg
        else:
            error_msg = f"""❌ FALHA NA VERIFICAÇÃO!

Detalhes:
- Documento: {document['document_name']}
- Erro: {verification_result['error']}
- Status: ASSINATURA INVÁLIDA

ATENÇÃO: Este documento pode ter sido alterado ou a assinatura é inválida."""
            return False, error_msg

    except Exception as e:
        conn.rollback()
        return False, f"Erro ao verificar documento: {e}"
    finally:
        conn.close()

def get_verification_history(document_id, user_id):
    """
    Obtém histórico de verificações de um documento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verifica se o usuário tem acesso ao documento
        cursor.execute("SELECT 1 FROM documents WHERE document_id = ? AND (sender_id = ? OR receiver_id = ?)",
                       (document_id, user_id, user_id))
        if not cursor.fetchone():
            return [], "Documento não encontrado ou sem permissão."

        cursor.execute("""
            SELECT vl.result, vl.error_message, vl.verified_at,
                   u.nome as verifier_name, u.email as verifier_email
            FROM verification_logs vl
            JOIN users u ON vl.verifier_id = u.user_id
            WHERE vl.document_id = ?
            ORDER BY vl.verified_at DESC
        """, (document_id,))
        history = []
        for row in cursor.fetchall():
            history.append({
                "result": row["result"],
                "error_message": row["error_message"],
                "verified_at": row["verified_at"],
                "verifier_name": row["verifier_name"],
                "verifier_email": row["verifier_email"]
            })
        return history, None
    finally:
        conn.close()

def get_document_statistics(user_id):
    """
    Obtém estatísticas dos documentos do usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Documentos enviados
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE sender_id = ?", (user_id,))
        sent_count = cursor.fetchone()["count"]
        
        # Documentos recebidos
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE receiver_id = ?", (user_id,))
        received_count = cursor.fetchone()["count"]
        
        # Documentos verificados (enviados)
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE sender_id = ? AND status = 'verified'", (user_id,))
        verified_sent = cursor.fetchone()["count"]
        
        # Documentos verificados (recebidos)
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE receiver_id = ? AND status = 'verified'", (user_id,))
        verified_received = cursor.fetchone()["count"]
        
        return {
            "sent_count": sent_count,
            "received_count": received_count,
            "verified_sent": verified_sent,
            "verified_received": verified_received
        }
    finally:
        conn.close()

