#!/usr/bin/env python3
"""
Script para criar usuários de teste no sistema de assinatura digital
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, get_db_connection
from auth import register_user, verify_email_code
import sqlite3

def criar_usuarios_teste():
    """Cria usuários de teste para demonstração"""
    
    # Garante que as tabelas existam
    create_tables()
    
    usuarios = [
        {"nome": "João Silva", "email": "joao@teste.com", "senha": "123456"},
        {"nome": "Maria Santos", "email": "maria@teste.com", "senha": "123456"},
        {"nome": "Pedro Oliveira", "email": "pedro@teste.com", "senha": "123456"}
    ]
    
    print("Criando usuários de teste...")
    
    for usuario in usuarios:
        print(f"\nCriando usuário: {usuario['nome']} ({usuario['email']})")
        
        # Registra o usuário
        success, message, user_id = register_user(usuario['nome'], usuario['email'], usuario['senha'])
        
        if success:
            print(f"✅ {message}")
            
            # user_id já foi retornado pela função register_user
            # Busca o código de verificação mais recente
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code FROM email_verifications 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            
            code_data = cursor.fetchone()
            if code_data:
                code = code_data['code']
                
                # Verifica automaticamente o email
                verify_success, verify_message = verify_email_code(user_id, code)
                if verify_success:
                    print(f"✅ Email verificado automaticamente")
                else:
                    print(f"❌ Erro na verificação: {verify_message}")
            else:
                print("❌ Código de verificação não encontrado")
            
            conn.close()
        else:
            if "já cadastrado" in message:
                print(f"ℹ️ Usuário já existe: {usuario['email']}")
            else:
                print(f"❌ Erro: {message}")
    
    print("\n" + "="*50)
    print("USUÁRIOS DE TESTE CRIADOS:")
    print("="*50)
    
    # Lista todos os usuários
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, nome, email, email_verified FROM users ORDER BY user_id")
    users = cursor.fetchall()
    
    for user in users:
        status = "✅ Verificado" if user['email_verified'] else "❌ Não verificado"
        print(f"ID: {user['user_id']} | {user['nome']} | {user['email']} | {status}")
    
    conn.close()
    
    print("\nSenha para todos os usuários: 123456")
    print("Agora você pode testar o sistema com múltiplos usuários!")

if __name__ == "__main__":
    criar_usuarios_teste()

