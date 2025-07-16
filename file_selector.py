"""
Módulo para seleção de arquivos via interface gráfica
"""
import os
import tkinter as tk
from tkinter import filedialog

def select_file(title="Selecionar Arquivo", filetypes=None):
    """
    Abre uma janela de seleção de arquivo e retorna o caminho selecionado.
    
    Args:
        title (str): Título da janela de seleção
        filetypes (list): Lista de tipos de arquivo permitidos
                         Ex: [("Documentos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
    
    Returns:
        str: Caminho do arquivo selecionado ou None se cancelado
    """
    # Cria uma janela root invisível
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    
    # Define tipos de arquivo padrão se não especificado
    if filetypes is None:
        filetypes = [
            ("Documentos de texto", "*.txt"),
            ("Documentos PDF", "*.pdf"),
            ("Documentos Word", "*.doc;*.docx"),
            ("Imagens", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("Todos os arquivos", "*.*")
        ]
    
    try:
        # Abre o diálogo de seleção de arquivo
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes
        )
        
        # Retorna o caminho ou None se cancelado
        return file_path if file_path else None
        
    except Exception as e:
        print(f"Erro ao abrir seletor de arquivos: {e}")
        return None
    finally:
        # Destrói a janela root
        root.destroy()

def select_multiple_files(title="Selecionar Arquivos", filetypes=None):
    """
    Abre uma janela de seleção múltipla de arquivos.
    
    Args:
        title (str): Título da janela de seleção
        filetypes (list): Lista de tipos de arquivo permitidos
    
    Returns:
        list: Lista de caminhos dos arquivos selecionados
    """
    root = tk.Tk()
    root.withdraw()
    
    if filetypes is None:
        filetypes = [
            ("Documentos de texto", "*.txt"),
            ("Documentos PDF", "*.pdf"),
            ("Documentos Word", "*.doc;*.docx"),
            ("Imagens", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
            ("Todos os arquivos", "*.*")
        ]
    
    try:
        file_paths = filedialog.askopenfilenames(
            title=title,
            filetypes=filetypes
        )
        
        return list(file_paths) if file_paths else []
        
    except Exception as e:
        print(f"Erro ao abrir seletor de arquivos: {e}")
        return []
    finally:
        root.destroy()

def select_directory(title="Selecionar Diretório"):
    """
    Abre uma janela de seleção de diretório.
    
    Args:
        title (str): Título da janela de seleção
    
    Returns:
        str: Caminho do diretório selecionado ou None se cancelado
    """
    root = tk.Tk()
    root.withdraw()
    
    try:
        dir_path = filedialog.askdirectory(title=title)
        return dir_path if dir_path else None
        
    except Exception as e:
        print(f"Erro ao abrir seletor de diretório: {e}")
        return None
    finally:
        root.destroy()

# Função alternativa para ambientes sem interface gráfica
def select_file_terminal():
    """
    Seleção de arquivo via terminal (fallback para ambientes sem GUI)
    """
    print("\n=== SELEÇÃO DE ARQUIVO ===")
    print("Digite o caminho completo do arquivo:")
    
    while True:
        file_path = input("Caminho do arquivo: ").strip()
        
        if not file_path:
            print("Caminho não pode estar vazio.")
            continue
            
        if not os.path.exists(file_path):
            print("Arquivo não encontrado. Verifique o caminho.")
            continue
            
        if not os.path.isfile(file_path):
            print("O caminho especificado não é um arquivo.")
            continue
            
        return file_path

def get_file_path(use_gui=True):
    """
    Função principal para obter caminho de arquivo.
    Tenta usar GUI primeiro, depois fallback para terminal.
    
    Args:
        use_gui (bool): Se deve tentar usar interface gráfica
    
    Returns:
        str: Caminho do arquivo selecionado ou None se cancelado
    """
    if use_gui:
        # Tenta usar interface gráfica
        file_path = select_file("Selecionar arquivo para assinar")
        if file_path:
            return file_path
        else:
            print("Seleção cancelada.")
            return None
    else:
        return select_file_terminal()

if __name__ == "__main__":
    # Teste do módulo
    print("Testando seleção de arquivo...")
    arquivo = get_file_path()
    if arquivo:
        print(f"Arquivo selecionado: {arquivo}")
    else:
        print("Nenhum arquivo selecionado.")

