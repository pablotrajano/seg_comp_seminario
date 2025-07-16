import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Calcula o máximo divisor comum (MDC) de a e b usando o algoritmo de Euclides
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# Algoritmo de Euclides Estendido:
# Retorna (g, x, y) tal que a*x + b*y = g = gcd(a, b)
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = extended_gcd(b % a, a)
    return g, y1 - (b // a) * x1, x1

# Calcula o inverso modular de a mod m (isto é, x tal que a*x ≡ 1 mod m)
def mod_inverse(a, m):
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise Exception("Modular inverse does not exist")  # a e m não são coprimos
    return x % m

# Teste de primalidade de Miller-Rabin (probabilístico)
def is_prime_miller_rabin(n, k=5):
    if n < 2 or n % 2 == 0:
        return False  # Desconsidera números < 2 ou pares (exceto 2)

    # Escreve n - 1 como 2^r * d, com d ímpar
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Executa k testes de testemunhas aleatórias
    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2  # a ∈ [2, n - 2]
        x = pow(a, d, n)  # x = a^d mod n
        if x == 1 or x == n - 1:
            continue  # Aparentemente primo nessa base

        # Tenta encontrar evidência de que n é composto
        for _ in range(r - 1):
            x = pow(x, 2, n)  # Eleva ao quadrado sucessivamente
            if x == n - 1:
                break  # Ainda pode ser primo
        else:
            return False  # Com certeza composto

    return True  # Provavelmente primo

# Gera um número primo com um número de bits específico
def generate_prime(bits):
    while True:
        # Gera número aleatório com 'bits' bits, garantindo que o primeiro e último bits sejam 1
        # (ou seja, número ímpar com bit mais significativo ligado → evita números menores)
        p = secrets.randbits(bits) | (1 << bits - 1) | 1
        if is_prime_miller_rabin(p):  # Testa se é provavelmente primo
            return p

# Novas funções para criptografia simétrica das chaves privadas
def derive_key_from_password(password, salt):
    """Deriva chave de criptografia a partir da senha do usuário"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_private_key(private_key_pem, password):
    """Criptografa a chave privada usando a senha do usuário"""
    salt = secrets.token_bytes(16)
    key = derive_key_from_password(password, salt)
    
    fernet = Fernet(key)
    encrypted_key = fernet.encrypt(private_key_pem.encode())
    
    # Retorna salt + chave criptografada em base64
    return base64.b64encode(salt + encrypted_key).decode()

def decrypt_private_key(encrypted_key_b64, password):
    """Descriptografa a chave privada usando a senha do usuário"""
    try:
        encrypted_data = base64.b64decode(encrypted_key_b64)
        salt = encrypted_data[:16]
        encrypted_key = encrypted_data[16:]
        
        key = derive_key_from_password(password, salt)
        fernet = Fernet(key)
        
        return fernet.decrypt(encrypted_key).decode()
    except Exception as e:
        raise ValueError("Senha incorreta ou dados corrompidos")


