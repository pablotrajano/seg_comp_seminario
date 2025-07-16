import os
import sys
import time
from auth import register_user, login_user, verify_email_code, get_all_users_except_current
from document_manager import (
    sign_and_send_document, get_sent_documents, get_received_documents, 
    verify_document, get_document_details, get_verification_history,
    get_document_statistics
)

CURRENT_USER = None

def clear_screen():
    """Limpa a tela do terminal"""
    os.system("cls" if os.name == "nt" else "clear")

def display_message(message, message_type="info"):
    """Exibe mensagem formatada com tipo específico"""
    if message_type == "info":
        print(f"\n[INFO] {message}")
    elif message_type == "success":
        print(f"\n[✅ SUCESSO] {message}")
    elif message_type == "error":
        print(f"\n[❌ ERRO] {message}")
    elif message_type == "warning":
        print(f"\n[⚠️ AVISO] {message}")
    
    input("\nPressione Enter para continuar...")

def get_user_input(prompt, sensitive=False):
    """Obtém entrada do usuário, com opção para entrada sensível"""
    if sensitive:
        import getpass
        return getpass.getpass(prompt)
    return input(prompt)

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def auth_menu():
    """Menu de autenticação (login/registro)"""
    while True:
        clear_screen()
        print_header("SISTEMA DE ASSINATURA DIGITAL RSA-PSS")
        print("""
🔐 AUTENTICAÇÃO

1. Fazer Login
2. Cadastrar Novo Usuário
0. Sair do Sistema
""")
        choice = get_user_input("Escolha uma opção: ").strip()

        if choice == "1":
            handle_login()
            if CURRENT_USER:
                break
        elif choice == "2":
            handle_register()
        elif choice == "0":
            display_message("Saindo do sistema. Até logo!", "info")
            sys.exit()
        else:
            display_message("Opção inválida. Tente novamente.", "error")

def handle_login():
    """Gerencia o processo de login"""
    global CURRENT_USER
    clear_screen()
    print_header("LOGIN")
    
    email = get_user_input("Email: ").strip()
    password = get_user_input("Senha: ", sensitive=True).strip()

    success, message, user_data = login_user(email, password)
    if success:
        CURRENT_USER = user_data
        display_message(f"Bem-vindo(a), {user_data['nome']}!", "success")
    else:
        display_message(message, "error")
        if user_data:  # user_data aqui é user_id se email não verificado
            handle_email_verification(user_data)

def handle_register():
    """Gerencia o processo de registro"""
    clear_screen()
    print_header("CADASTRO DE NOVO USUÁRIO")
    
    nome = get_user_input("Nome completo: ").strip()
    email = get_user_input("Email: ").strip()
    password = get_user_input("Senha: ", sensitive=True).strip()
    confirm_password = get_user_input("Confirme a senha: ", sensitive=True).strip()

    if password != confirm_password:
        display_message("As senhas não coincidem.", "error")
        return

    success, message, user_id = register_user(nome, email, password)
    if success:
        print(f"\n[✅ SUCESSO] {message}")
        input("\nPressione Enter para continuar...")
        # Vai direto para verificação de email com o user_id retornado
        handle_email_verification(user_id)
    else:
        display_message(message, "error")

def handle_email_verification(user_id):
    """Gerencia a verificação de email"""
    clear_screen()
    print_header("VERIFICAÇÃO DE EMAIL")
    print("Um código de 6 dígitos foi enviado para seu email.")
    print("O código expira em 1 minuto.")
    
    code = get_user_input("Código de verificação: ").strip()
    success, message = verify_email_code(user_id, code)
    display_message(message, "success" if success else "error")

def main_menu():
    """Menu principal do sistema"""
    while True:
        clear_screen()
        stats = get_document_statistics(CURRENT_USER['user_id'])
        
        print_header(f"MENU PRINCIPAL - {CURRENT_USER['nome']}")
        print(f"""
👤 Usuário: {CURRENT_USER['nome']} ({CURRENT_USER['email']})

📊 ESTATÍSTICAS:
   • Documentos enviados: {stats['sent_count']} (verificados: {stats['verified_sent']})
   • Documentos recebidos: {stats['received_count']} (verificados: {stats['verified_received']})

📋 OPÇÕES:
1. 📝 Assinar e Enviar Documento
2. 📤 Ver Documentos Enviados
3. 📥 Ver Documentos Recebidos
0. 🚪 Sair do Sistema
""")
        choice = get_user_input("Escolha uma opção: ").strip()

        if choice == "1":
            handle_sign_and_send_document()
        elif choice == "2":
            handle_view_sent_documents()
        elif choice == "3":
            handle_view_received_documents()
        elif choice == "0":
            display_message("Saindo do sistema. Até logo!", "info")
            sys.exit()
        else:
            display_message("Opção inválida. Tente novamente.", "error")

def handle_sign_and_send_document():
    """Gerencia assinatura e envio de documento"""
    clear_screen()
    print_header("ASSINAR E ENVIAR DOCUMENTO")
    
    document_name = get_user_input("Título do documento: ").strip()
    if not document_name:
        display_message("Título não pode estar vazio.", "error")
        return
    
    user_password = get_user_input("Sua senha (para criptografar chave privada): ", sensitive=True).strip()
    if not user_password:
        display_message("Senha é obrigatória.", "error")
        return

    # Lista usuários disponíveis
    users = get_all_users_except_current(CURRENT_USER["user_id"])
    if not users:
        display_message("Não há outros usuários cadastrados para enviar documentos.", "warning")
        return

    print("\n📋 DESTINATÁRIOS DISPONÍVEIS:")
    for i, user in enumerate(users):
        print(f"{i+1}. {user['nome']} ({user['email']})")
    
    while True:
        try:
            receiver_choice = int(get_user_input("\nEscolha o número do destinatário: "))
            if 1 <= receiver_choice <= len(users):
                selected_receiver = users[receiver_choice - 1]
                break
            else:
                print("Escolha inválida. Tente novamente.")
        except ValueError:
            print("Digite um número válido.")

    print(f"\n📤 Enviando para: {selected_receiver['nome']} ({selected_receiver['email']})")
    
    # Pergunta sobre interface gráfica
    use_gui_input = get_user_input("Usar interface gráfica para seleção de arquivo? (s/n): ").strip().lower()
    use_gui = use_gui_input in ['s', 'sim', 'y', 'yes']

    success, message = sign_and_send_document(
        CURRENT_USER["user_id"],
        CURRENT_USER["email"],
        selected_receiver["user_id"],
        selected_receiver["email"],
        document_name,
        user_password,
        use_gui=use_gui
    )
    
    display_message(message, "success" if success else "error")

def handle_view_sent_documents():
    """Visualiza documentos enviados"""
    clear_screen()
    print_header("DOCUMENTOS ENVIADOS")
    
    documents = get_sent_documents(CURRENT_USER["user_id"])
    if not documents:
        display_message("Você não enviou nenhum documento ainda.", "info")
        return

    print("\n📤 SEUS DOCUMENTOS ENVIADOS:\n")
    for i, doc in enumerate(documents):
        status_icon = "✅" if doc['status'] == 'verified' else "📤" if doc['status'] == 'sent' else "❌"
        print(f"{i+1}. {status_icon} {doc['document_name']}")
        print(f"   📧 Para: {doc['receiver_name']} ({doc['receiver_email']})")
        print(f"   📅 Enviado: {doc['created_at']}")
        print(f"   📊 Status: {doc['status'].upper()}")
        if doc['verified_at']:
            print(f"   ✅ Verificado: {doc['verified_at']}")
        print(f"   🆔 ID: {doc['document_id']}")
        print()
    
    input("Pressione Enter para voltar ao menu principal.")

def handle_view_received_documents():
    """Visualiza documentos recebidos"""
    clear_screen()
    print_header("DOCUMENTOS RECEBIDOS")
    
    documents = get_received_documents(CURRENT_USER["user_id"])
    if not documents:
        display_message("Você não recebeu nenhum documento ainda.", "info")
        return

    print("\n📥 DOCUMENTOS RECEBIDOS:\n")
    for i, doc in enumerate(documents):
        status_icon = "✅" if doc['status'] == 'verified' else "📥" if doc['status'] == 'sent' else "❌"
        print(f"{i+1}. {status_icon} {doc['document_name']}")
        print(f"   📧 De: {doc['sender_name']} ({doc['sender_email']})")
        print(f"   📅 Recebido: {doc['created_at']}")
        print(f"   📊 Status: {doc['status'].upper()}")
        if doc['verified_at']:
            print(f"   ✅ Verificado: {doc['verified_at']}")
        print(f"   🆔 ID: {doc['document_id']}")
        print()
    
    while True:
        choice = get_user_input("Digite o número do documento para verificar (0 para voltar): ").strip()
        if choice == "0":
            break
        try:
            doc_index = int(choice) - 1
            if 0 <= doc_index < len(documents):
                selected_doc_id = documents[doc_index]["document_id"]
                handle_verify_document(selected_doc_id)
                break
            else:
                print("Escolha inválida. Tente novamente.")
        except ValueError:
            print("Digite um número válido.")

def handle_verify_document(document_id):
    """Verifica um documento específico"""
    clear_screen()
    print_header("VERIFICAÇÃO DE ASSINATURA")
    
    doc_details = get_document_details(document_id, CURRENT_USER["user_id"])
    if not doc_details:
        display_message("Documento não encontrado ou sem permissão.", "error")
        return

    print(f"📄 Documento: {doc_details['document_name']}")
    print(f"📧 Remetente: {doc_details['sender_name']} ({doc_details['sender_email']})")
    print(f"📅 Data de envio: {doc_details['created_at']}")
    print(f"📊 Status atual: {doc_details['status'].upper()}")
    
    # Mostra prévia do conteúdo
    content_preview = doc_details["document_content"][:200]
    if len(doc_details["document_content"]) > 200:
        content_preview += "..."
    print(f"\n📝 Prévia do conteúdo:\n{content_preview}")

    confirm = get_user_input("\n🔍 Deseja verificar a assinatura deste documento? (s/n): ").strip().lower()
    if confirm in ['s', 'sim', 'y', 'yes']:
        success, message = verify_document(document_id, CURRENT_USER["user_id"])
        display_message(message, "success" if success else "error")
        
        # Exibe histórico de verificação
        history, error = get_verification_history(document_id, CURRENT_USER["user_id"])
        if error:
            display_message(f"Erro ao carregar histórico: {error}", "error")
        elif history:
            print("\n📋 HISTÓRICO DE VERIFICAÇÕES:")
            print("-" * 50)
            for entry in history:
                status = "✅ VÁLIDA" if entry["result"] == "verified" else "❌ INVÁLIDA"
                print(f"• {status}")
                print(f"  👤 Verificado por: {entry['verifier_name']} ({entry['verifier_email']})")
                print(f"  📅 Data: {entry['verified_at']}")
                if entry["error_message"]:
                    print(f"  ⚠️ Erro: {entry['error_message']}")
                print()
            input("Pressione Enter para continuar...")

def show_system_info():
    """Mostra informações do sistema"""
    clear_screen()
    print_header("INFORMAÇÕES DO SISTEMA")
    print("""
🔐 SISTEMA DE ASSINATURA DIGITAL RSA-PSS

📋 Características:
• Algoritmo: RSA-PSS (Probabilistic Signature Scheme)
• Hash: SHA3-256
• Tamanho da chave: 2048 bits
• Banco de dados: SQLite
• Interface: Terminal com seleção gráfica de arquivos

🛡️ Segurança:
• Chaves únicas por documento
• Chaves privadas criptografadas com senha do usuário
• Verificação de integridade via hash
• Logs de verificação para auditoria

👨‍💻 Desenvolvido para o seminário de Segurança Computacional
""")
    input("Pressione Enter para continuar...")

if __name__ == "__main__":
    try:
        # Garante que as tabelas do banco de dados existam
        from database import create_tables
        create_tables()
        
        # Mostra informações do sistema
        show_system_info()
        
        # Inicia o fluxo de autenticação
        auth_menu()
        
        # Se autenticado, vai para o menu principal
        if CURRENT_USER:
            main_menu()
            
    except KeyboardInterrupt:
        print("\n\nSistema interrompido pelo usuário. Até logo!")
        sys.exit()
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)

