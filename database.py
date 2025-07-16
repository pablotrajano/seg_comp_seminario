import sqlite3
from datetime import datetime

DATABASE_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha_hash VARCHAR(255) NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
    ''')

    # Tabela de verificações de email
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_verifications (
            verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code VARCHAR(6) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    ''')

    # Tabela de documentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            document_id VARCHAR(36) PRIMARY KEY,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            document_name VARCHAR(255) NOT NULL,
            document_content TEXT NOT NULL,
            document_hash VARCHAR(64) NOT NULL,
            public_key TEXT NOT NULL,
            private_key_encrypted TEXT NOT NULL,
            signature TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'sent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    ''')

    # Tabela de logs de verificação
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id VARCHAR(36) NOT NULL,
            verifier_id INTEGER NOT NULL,
            result VARCHAR(20) NOT NULL,
            error_message TEXT,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
            FOREIGN KEY (verifier_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print(f"Banco de dados '{DATABASE_NAME}' e tabelas criadas com sucesso.")


