import base64
import os
import secrets
import uuid
from crypto.crypto_utils import generate_prime, gcd, mod_inverse, encrypt_private_key

# Gera um par de chaves RSA (pública e privada)
def generate_rsa_keys(bits=2048):
    # Gera dois primos grandes p e q com metade do tamanho total de bits
    p = generate_prime(bits // 2)
    q = generate_prime(bits // 2)

    # Garante que p e q sejam diferentes (por segurança)
    while p == q:
        q = generate_prime(bits // 2)

    # n = p * q é o módulo usado em ambas as chaves
    n = p * q

    # phi é a função totiente de Euler: (p-1)*(q-1)
    phi = (p - 1) * (q - 1)

    # e é o expoente público (valor fixo comum), usado na chave pública
    e = 65537

    # Garante que e e phi sejam coprimos (necessário para que exista inverso)
    while gcd(e, phi) != 1:
        e = secrets.randbelow(phi - 2) + 2  # Escolhe outro e aleatório se necessário

    # d é o inverso modular de e mod phi, usado na chave privada
    d = mod_inverse(e, phi)

    # Retorna as chaves nos formatos (n, e) e (n, d)
    return (n, e), (n, d)

# Codifica uma chave (n, expoente) em uma string com base64 e delimitadores
def serialize_key(key_tuple, key_type):
    n, exp = key_tuple
    key_str = f"-----BEGIN {key_type} KEY-----\n"
    # Codifica a string "n:<valor>,exp:<valor>" em Base64
    key_str += base64.b64encode(f"n:{n},exp:{exp}".encode()).decode()
    key_str += f"\n-----END {key_type} KEY-----"
    return key_str

# Lê uma chave no formato serializado e retorna a tupla (n, expoente)
def deserialize_key(key_str, key_type):
    lines = key_str.split("\n")

    # Valida se o formato da chave está correto (linhas de cabeçalho e rodapé)
    if not (lines[0] == f"-----BEGIN {key_type} KEY-----" and lines[2] == f"-----END {key_type} KEY-----"):
        raise ValueError("Formato inválido")

    # Decodifica a linha Base64 e extrai os valores de n e exp
    n, exp = [int(x.split(":")[1]) for x in base64.b64decode(lines[1]).decode().split(",")]
    return (n, exp)

def generate_document_keys(user_password):
    """
    Gera par de chaves RSA específico para um documento.
    Retorna: (public_key_pem, private_key_encrypted, document_id, public_key_tuple, private_key_tuple)
    """
    document_id = str(uuid.uuid4())
    
    public_key_tuple, private_key_tuple = generate_rsa_keys()
    
    public_key_pem = serialize_key(public_key_tuple, "PUBLIC")
    private_key_pem = serialize_key(private_key_tuple, "PRIVATE")
    
    private_key_encrypted = encrypt_private_key(private_key_pem, user_password)
    
    return public_key_pem, private_key_encrypted, document_id, public_key_tuple, private_key_tuple


