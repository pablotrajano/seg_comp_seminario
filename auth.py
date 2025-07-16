import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta
from database import get_db_connection

# Função para hash de senha
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Função para verificar senha
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

# Função para simular envio de email (para testes)
def send_verification_email(email, code):
    print(f"\n[SIMULADO] Enviando código de verificação para {email}: {code}")
    print("Este código expira em 1 minuto.")

# Função de registro de usuário
def register_user(nome, email, senha):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False, "Email já cadastrado.", None

        hashed_senha = hash_password(senha)
        cursor.execute("INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                       (nome, email, hashed_senha))
        user_id = cursor.lastrowid

        code = str(secrets.randbelow(900000) + 100000)  # Código de 6 dígitos
        expires_at = datetime.now() + timedelta(minutes=1)
        cursor.execute("INSERT INTO email_verifications (user_id, code, expires_at) VALUES (?, ?, ?)",
                       (user_id, code, expires_at))
        conn.commit()

        send_verification_email(email, code)
        return True, f"Usuário cadastrado com sucesso! ID: {user_id}. Verifique seu email para ativar a conta.", user_id

    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Erro ao registrar usuário: {e}", None
    finally:
        conn.close()

# Função de login de usuário
def login_user(email, senha):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id, nome, senha_hash, email_verified FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            return False, "Email ou senha incorretos.", None

        user_id, nome, hashed_senha, email_verified = user

        if not check_password(senha, hashed_senha):
            return False, "Email ou senha incorretos.", None

        if not email_verified:
            # Gera um novo código de verificação se o email não estiver verificado
            code = str(secrets.randbelow(900000) + 100000)
            expires_at = datetime.now() + timedelta(minutes=1)
            cursor.execute("INSERT INTO email_verifications (user_id, code, expires_at) VALUES (?, ?, ?)",
                           (user_id, code, expires_at))
            conn.commit()
            send_verification_email(email, code)
            return False, "Email não verificado. Um novo código foi enviado para seu email.", user_id

        cursor.execute("UPDATE users SET last_login = ? WHERE user_id = ?", (datetime.now(), user_id))
        conn.commit()
        return True, "Login realizado com sucesso!", {"user_id": user_id, "nome": nome, "email": email}

    except sqlite3.Error as e:
        return False, f"Erro ao fazer login: {e}", None
    finally:
        conn.close()

# Função para verificar código de email
def verify_email_code(user_id, code):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT verification_id, expires_at FROM email_verifications WHERE user_id = ? AND code = ? AND verified_at IS NULL ORDER BY created_at DESC LIMIT 1",
                       (user_id, code))
        verification = cursor.fetchone()

        if not verification:
            return False, "Código inválido ou não encontrado."

        verification_id, expires_at_str = verification
        expires_at = datetime.strptime(expires_at_str, 
                                       "%Y-%m-%d %H:%M:%S.%f") if "." in expires_at_str else datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")

        if datetime.now() > expires_at:
            return False, "Código expirado."

        cursor.execute("UPDATE email_verifications SET verified_at = ? WHERE verification_id = ?",
                       (datetime.now(), verification_id))
        cursor.execute("UPDATE users SET email_verified = TRUE WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, "Email verificado com sucesso!"

    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Erro ao verificar email: {e}"
    finally:
        conn.close()

# Função para obter usuário por ID
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id, nome, email, email_verified FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return {"user_id": user[0], "nome": user[1], "email": user[2], "email_verified": bool(user[3])}
        return None
    finally:
        conn.close()

# Função para obter todos os usuários (para seleção de destinatário)
def get_all_users_except_current(current_user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id, nome, email FROM users WHERE user_id != ? AND email_verified = TRUE", (current_user_id,))
        users = []
        for row in cursor.fetchall():
            users.append({"user_id": row[0], "nome": row[1], "email": row[2]})
        return users
    finally:
        conn.close()

