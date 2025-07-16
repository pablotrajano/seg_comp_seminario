import base64
import hashlib
import json
from datetime import datetime
from crypto.signature import sha3_256_hash, xor_bytes, mgf1
from crypto.keygen import deserialize_key

def parse_signature(b64_sig):
    return int.from_bytes(base64.b64decode(b64_sig), "big")

def rsa_pss_verify(message, b64_sig, public_key, em_len):
    sig_int = parse_signature(b64_sig)
    em = pow(sig_int, public_key[1], public_key[0]).to_bytes(em_len, "big")
    h_len = 32

    if em[-1] != 0xbc:
        return False
    h = em[-h_len-1:-1]
    masked_db = em[:em_len - h_len - 1]
    db = xor_bytes(masked_db, mgf1(h, len(masked_db), h_len))

    try:
        sep_index = db.index(b"\x01")
    except ValueError:
        return False

    if any(b != 0 for b in db[:sep_index]):
        return False

    salt = db[sep_index+1:]
    m_hash = sha3_256_hash(message)
    m_prime = b"\x00" * 8 + m_hash + salt
    return h == hashlib.sha3_256(m_prime).digest()

def verify_signed_document(signature_package, public_key_pem):
    """
    Verifica um documento assinado usando o pacote de assinatura
    """
    try:
        # Extrai dados do pacote
        document_content_b64 = signature_package["document_content"]
        document_hash_b64 = signature_package["document_hash"]
        signature_b64 = signature_package["signature"]
        
        # Decodifica conteúdo do documento
        try:
            document_content = base64.b64decode(document_content_b64).decode('utf-8')
        except UnicodeDecodeError:
            # Se não conseguir decodificar como UTF-8, trata como binário
            document_content_bytes = base64.b64decode(document_content_b64)
            # Para verificação, usa o conteúdo em base64 como string
            document_content = document_content_b64
        
        # Deserializa chave pública
        public_key = deserialize_key(public_key_pem, "PUBLIC")
        
        # Calcula tamanho da assinatura
        em_len = (public_key[0].bit_length() + 7) // 8
        
        # Verifica integridade do documento
        if isinstance(document_content, str) and document_content == document_content_b64:
            # Conteúdo binário - usa os bytes originais para hash
            calculated_hash = sha3_256_hash(base64.b64decode(document_content_b64))
        else:
            # Conteúdo texto - usa a string para hash
            calculated_hash = sha3_256_hash(document_content)
            
        stored_hash = base64.b64decode(document_hash_b64)
        
        if calculated_hash != stored_hash:
            return {
                "valid": False,
                "error": "Documento foi alterado após a assinatura",
                "details": None
            }
        
        # Para verificação da assinatura, usa o conteúdo original
        if isinstance(document_content, str) and document_content == document_content_b64:
            # Conteúdo binário - converte para string base64 para assinatura
            content_for_signature = document_content_b64
        else:
            # Conteúdo texto
            content_for_signature = document_content
        
        # Verifica assinatura
        is_valid = rsa_pss_verify(content_for_signature, signature_b64, public_key, em_len)
        
        if is_valid:
            return {
                "valid": True,
                "error": None,
                "details": {
                    "sender_email": signature_package.get("sender_email"),
                    "timestamp": signature_package.get("timestamp"),
                    "document_content": document_content if isinstance(document_content, str) and document_content != document_content_b64 else "Conteúdo binário",
                    "algorithm": signature_package.get("algorithm", "RSA-PSS"),
                    "hash_algorithm": signature_package.get("hash_algorithm", "SHA3-256")
                }
            }
        else:
            return {
                "valid": False,
                "error": "Assinatura digital inválida",
                "details": None
            }
            
    except Exception as e:
        return {
            "valid": False,
            "error": f"Erro ao verificar documento: {str(e)}",
            "details": None
        }


