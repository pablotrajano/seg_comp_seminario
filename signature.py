import hashlib
import secrets
import base64
import json
from datetime import datetime

# Gera o hash SHA3-256 da mensagem de entrada (em bytes)
def sha3_256_hash(msg):
    if isinstance(msg, str):
        return hashlib.sha3_256(msg.encode()).digest()
    return hashlib.sha3_256(msg).digest()

# Máscara determinística baseada em SHA3-256, usada no esquema PSS (Mask Generation Function 1)
def mgf1(seed, mask_len, h_len):
    T = b""
    # Gera blocos de hash até alcançar o comprimento desejado
    for i in range((mask_len + h_len - 1) // h_len):
        T += hashlib.sha3_256(seed + i.to_bytes(4, "big")).digest()
    return T[:mask_len]

# Aplica operação XOR byte a byte entre dois blocos de bytes
def xor_bytes(b1, b2):
    return bytes(x ^ y for x, y in zip(b1, b2))

# Codifica a mensagem usando o esquema PSS (Probabilistic Signature Scheme)
def pss_encode(m_hash, em_len, salt_len=32):
    h_len = len(m_hash)

    # Verifica se o tamanho é suficiente para o encoding
    if em_len < h_len + salt_len + 2:
        raise ValueError("EM too short")  # Tamanho insuficiente para a estrutura

    # Gera um valor aleatório chamado salt (sal)
    salt = secrets.token_bytes(salt_len)

    # Concatena 8 bytes zeros, o hash da mensagem e o salt → m\'
    m_prime = b"\x00" * 8 + m_hash + salt

    # Hash de m\'
    h = hashlib.sha3_256(m_prime).digest()

    # PS: padding com zeros; DB: PS || 0x01 || salt
    ps = b"\x00" * (em_len - salt_len - h_len - 2)
    db = ps + b"\x01" + salt

    # Aplica máscara sobre DB
    masked_db = xor_bytes(db, mgf1(h, len(db), h_len))

    # Concatena partes finais: maskedDB || H || 0xbc
    return masked_db + h + b"\xbc"

# Realiza a assinatura da mensagem com chave privada usando RSA-PSS
def rsa_pss_sign(message, private_key, em_len, salt_len=32):
    # Codifica a mensagem com PSS
    em = pss_encode(sha3_256_hash(message), em_len, salt_len)

    # Converte para inteiro e aplica operação RSA: sig = em^d mod n
    return pow(int.from_bytes(em, "big"), private_key[1], private_key[0])

# Converte a assinatura (inteiro) para Base64, com tamanho fixo
def format_signature(sig_int, em_len):
    return base64.b64encode(sig_int.to_bytes(em_len, "big")).decode()

def sign_document_content(document_content, private_key, sender_email, receiver_email):
    """
    Assina o conteúdo de um documento e retorna pacote completo
    """
    # Calcula hash do documento
    document_hash = sha3_256_hash(document_content)
    
    # Calcula tamanho da assinatura baseado na chave
    em_len = (private_key[0].bit_length() + 7) // 8
    
    # Gera assinatura
    signature_int = rsa_pss_sign(document_content, private_key, em_len)
    signature_b64 = format_signature(signature_int, em_len)
    
    # Cria pacote de assinatura
    signature_package = {
        "document_content": base64.b64encode(document_content.encode()).decode(),
        "document_hash": base64.b64encode(document_hash).decode(),
        "signature": signature_b64,
        "sender_email": sender_email,
        "receiver_email": receiver_email,
        "timestamp": datetime.now().isoformat(),
        "algorithm": "RSA-PSS",
        "hash_algorithm": "SHA3-256"
    }
    
    return signature_package


