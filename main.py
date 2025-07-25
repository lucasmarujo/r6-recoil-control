import threading
import random
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
import ctypes
from ctypes import wintypes
import keyboard  # Biblioteca mais confiável para capturar teclas


# Configurações do Windows API para controle do mouse e teclado
user32 = ctypes.windll.user32
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_F9 = 0x78  # Código virtual da tecla F9

# Para registrar a tecla globalmente
WM_HOTKEY = 0x0312
MOD_NONE = 0x0000

# Definições para mensagens do Windows
class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]

# Classe para representar um perfil de configuração
class Perfil:
    def __init__(self, nome, intensidade):
        self.nome = nome
        self.intensidade = intensidade
        self.ativo = False  # Estado do perfil (ativo/inativo)
        self.check_var = None  # Variável para o Checkbutton
        self.label_intensidade = None  # Label para mostrar a intensidade
        self.label_nome = None  # Label para mostrar o nome
        self.frame = None  # Frame que contém este perfil

# Variáveis globais
holding = False
intensity = 5  # valor padrão
running = False  # Variável para controlar se o script está em execução
start_button = None  # Referência para o botão
status_label = None  # Referência para o label de status
root = None  # Referência para a janela principal
monitor_thread = None  # Thread de monitoramento do mouse
recoil_thread = None  # Thread de controle de recoil
current_profile = None  # Perfil atualmente selecionado
profiles = []  # Lista de perfis disponíveis
profiles_frame = None  # Frame que contém todos os perfis

# Função que move o mouse
def move_mouse(dx, dy):
    user32.mouse_event(MOUSEEVENTF_MOVE, ctypes.c_long(dx), ctypes.c_long(dy), 0, 0)

# Função para simular movimentos humanos
def simulate_human_movement():
    dy = random.randint(3, 6)
    delay = random.uniform(0.01, 0.03)
    move_mouse(0, dy)
    time.sleep(delay)

# Função que monitora o botão do mouse
def mouse_monitor():
    global holding, running
    
    # Referência para o estado do botão anterior
    previous_state = False
    
    while running:
        # Verifica o estado do botão esquerdo do mouse (0x01 = botão esquerdo)
        current_state = user32.GetAsyncKeyState(0x01) & 0x8000 != 0
        
        # Mudança de estado: solto -> pressionado
        if current_state and not previous_state:
            holding = True
        # Mudança de estado: pressionado -> solto
        elif not current_state and previous_state:
            holding = False
            
        previous_state = current_state
        time.sleep(0.01)  # Pequeno delay para reduzir o uso de CPU

# Função que controla o recoil com randomização avançada
def recoil_control():
    global holding, intensity, running, current_profile
    
    while running:
        if holding and current_profile:
            # Obtém a intensidade do perfil atual
            current_intensity = current_profile.intensidade
            
            # Randomização de intensidade base
            base_intensity = current_intensity * random.uniform(0.7, 1.3)
            
            # Simular micro-pausas aleatórias
            if random.random() < 0.15:  # 15% de chance de uma micro-pausa
                time.sleep(random.uniform(0.008, 0.025))
                continue
                
            # Varia a direção ligeiramente (principalmente vertical, mas um pouco horizontal)
            dx = random.uniform(-0.5, 0.5)
            dy = base_intensity
            
            # Padrão de movimento: às vezes faz movimentos mais curtos ou mais longos
            move_factor = 1.0
            if random.random() < 0.2:  # 20% de chance de variação significativa
                move_factor = random.uniform(0.5, 1.8)
                
            # Aplica o movimento
            move_mouse(int(dx), int(dy * move_factor))
            
            # Delay humanizado entre movimentos
            delay = random.uniform(0.01, 0.04)
            # Ocasionalmente insere delays um pouco maiores para simular ajustes humanos
            if random.random() < 0.1:  # 10% de chance
                delay = random.uniform(0.05, 0.12)
                
            time.sleep(delay)
        else:
            # Quando não está segurando o botão, espera um pouco mais
            time.sleep(0.05)

# Função para alternar o estado de execução do script
def toggle_script_state():
    global running, monitor_thread, recoil_thread
    running = not running
    
    # Atualizamos a interface se ela já existir
    if root and not root.winfo_ismapped():
        return  # Se a janela foi fechada, não fazemos nada
        
    if start_button and status_label:
        if running:
            start_button.config(text="Pausar", bg="#ff6666")
            status_label.config(text="Status: Ativo", fg="green")
            # Inicia as threads se não estiverem rodando
            if monitor_thread is None or not monitor_thread.is_alive():
                monitor_thread = threading.Thread(target=mouse_monitor, daemon=True)
                monitor_thread.start()
            if recoil_thread is None or not recoil_thread.is_alive():
                recoil_thread = threading.Thread(target=recoil_control, daemon=True)
                recoil_thread.start()
        else:
            start_button.config(text="Iniciar", bg="#4CAF50")
            status_label.config(text="Status: Parado", fg="red")

# Função para selecionar um perfil
def selecionar_perfil():
    global current_profile, profiles
    
    # Encontrar o perfil que foi clicado
    perfil_clicado = None
    for perfil in profiles:
        if perfil.check_var.get() == 1:
            perfil_clicado = perfil
            break
    
    # Se um perfil foi desmarcado e era o atual, desativa o perfil atual
    if perfil_clicado is None and current_profile is not None:
        current_profile = None
        return
        
    # Se um perfil foi marcado
    if perfil_clicado is not None:
        # Desmarcar todos os outros perfis
        for perfil in profiles:
            if perfil != perfil_clicado and perfil.check_var.get() == 1:
                perfil.check_var.set(0)
        
        # Definir o perfil atual
        current_profile = perfil_clicado

# Função para alterar a intensidade de um perfil
def alterar_intensidade(perfil):
    nova_intensidade = simpledialog.askinteger("Intensidade", 
                                              f"Nova intensidade para {perfil.nome}:",
                                              minvalue=0, maxvalue=30,
                                              initialvalue=perfil.intensidade)
    if nova_intensidade is not None:
        perfil.intensidade = nova_intensidade
        perfil.label_intensidade.config(text=f"Intensidade: {nova_intensidade}")

# Função para alterar o nome de um perfil
def alterar_nome(perfil):
    novo_nome = simpledialog.askstring("Nome", 
                                      "Novo nome para o perfil:",
                                      initialvalue=perfil.nome)
    if novo_nome and novo_nome.strip():
        perfil.nome = novo_nome.strip()
        perfil.label_nome.config(text=perfil.nome)

# Função para editar um perfil (nome e intensidade)
def editar_perfil(perfil):
    # Criar uma nova janela de diálogo
    dialog = tk.Toplevel()
    dialog.title(f"Editar Perfil: {perfil.nome}")
    dialog.geometry("300x150")
    dialog.resizable(False, False)
    dialog.grab_set()  # Torna a janela modal
    
    # Frame principal
    frame = tk.Frame(dialog, padx=10, pady=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Campos para nome e intensidade
    tk.Label(frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=5)
    nome_var = tk.StringVar(value=perfil.nome)
    nome_entry = tk.Entry(frame, textvariable=nome_var, width=20)
    nome_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(frame, text="Intensidade:").grid(row=1, column=0, sticky="w", pady=5)
    intensidade_var = tk.IntVar(value=perfil.intensidade)
    intensidade_entry = tk.Spinbox(frame, from_=0, to=30, textvariable=intensidade_var, width=5)
    intensidade_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # Função para salvar as alterações
    def salvar():
        novo_nome = nome_var.get().strip()
        nova_intensidade = intensidade_var.get()
        
        if novo_nome:
            perfil.nome = novo_nome
            perfil.label_nome.config(text=novo_nome)
            
        perfil.intensidade = nova_intensidade
        perfil.label_intensidade.config(text=f"Intensidade: {nova_intensidade}")
        
        dialog.destroy()
    
    # Função para cancelar
    def cancelar():
        dialog.destroy()
    
    # Botões
    botoes_frame = tk.Frame(frame)
    botoes_frame.grid(row=2, column=0, columnspan=2, pady=10)
    
    tk.Button(botoes_frame, text="Salvar", command=salvar, 
             bg="#4CAF50", fg="white", width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(botoes_frame, text="Cancelar", command=cancelar, 
             bg="#f44336", fg="white", width=10).pack(side=tk.LEFT, padx=5)

# Função para criar um novo perfil
def criar_novo_perfil():
    global profiles, profiles_frame
    
    nome = simpledialog.askstring("Novo Perfil", "Nome do perfil:")
    if nome:
        intensidade = simpledialog.askinteger("Intensidade", 
                                             "Intensidade para o perfil (0-30):",
                                             minvalue=0, maxvalue=30,
                                             initialvalue=5)
        if intensidade is not None:
            novo_perfil = Perfil(nome, intensidade)
            profiles.append(novo_perfil)
            adicionar_perfil_na_interface(novo_perfil, profiles_frame)

# Função para adicionar um perfil na interface
def adicionar_perfil_na_interface(perfil, frame):
    # Cria um frame para este perfil
    perfil.frame = tk.Frame(frame, bg="#f0f0f0", padx=5, pady=3)
    perfil.frame.pack(fill=tk.X, padx=5, pady=2)
    
    # Variável para o Checkbutton
    perfil.check_var = tk.IntVar()
    
    # Adiciona o Checkbutton, nome e intensidade
    check = tk.Checkbutton(perfil.frame, variable=perfil.check_var, 
                           command=selecionar_perfil, bg="#f0f0f0")
    check.pack(side=tk.LEFT)
    
    perfil.label_nome = tk.Label(perfil.frame, text=perfil.nome, bg="#f0f0f0", width=15, anchor="w")
    perfil.label_nome.pack(side=tk.LEFT, padx=5)
    
    perfil.label_intensidade = tk.Label(perfil.frame, text=f"Intensidade: {perfil.intensidade}", 
                                       bg="#f0f0f0", width=12)
    perfil.label_intensidade.pack(side=tk.LEFT, padx=5)
    
    # Botão para alterar a intensidade
    editar_btn = tk.Button(perfil.frame, text="Editar", 
                           command=lambda p=perfil: editar_perfil(p),
                           bg="#e0e0e0", width=8)
    editar_btn.pack(side=tk.RIGHT, padx=5)

# Interface com lista de perfis
def show_ui():
    global running, start_button, status_label, root, profiles, profiles_frame, current_profile
    
    def start_script():
        global running, monitor_thread, recoil_thread
        
        # Verifica se um perfil foi selecionado
        if current_profile is None:
            # Exibe mensagem de erro se nenhum perfil foi selecionado
            tk.messagebox.showerror("Erro", "Selecione um perfil antes de iniciar")
            return
            
        if not running:
            running = True
            start_button.config(text="Pausar", bg="#ff6666")
            status_label.config(text="Status: Ativo", fg="green")
            
            # Inicia o thread de controle de recoil
            recoil_thread = threading.Thread(target=recoil_control, daemon=True)
            recoil_thread.start()
            
            # Inicia o thread de monitoramento do mouse
            monitor_thread = threading.Thread(target=mouse_monitor, daemon=True)
            monitor_thread.start()
        else:
            stop_script()
    
    def stop_script():
        global running
        
        running = False
        start_button.config(text="Iniciar", bg="#4CAF50")
        status_label.config(text="Status: Parado", fg="red")
            
    def on_closing():
        global running
        running = False
        root.destroy()

    root = tk.Tk()
    root.title("ASR")
    root.geometry("400x500")
    root.configure(bg="#f0f0f0")
    
    # Frame principal
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Título
    tk.Label(main_frame, text="Assistente de Movimento", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=(0, 15))
    
    # Status
    status_label = tk.Label(main_frame, text="Status: Parado", fg="red", bg="#f0f0f0", font=("Arial", 10))
    status_label.pack(pady=(0, 10))
    
    # Frame para a lista de perfis
    list_frame = tk.Frame(main_frame, bg="#f0f0f0", bd=1, relief=tk.SOLID)
    list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Título da lista
    tk.Label(list_frame, text="Perfis disponíveis", bg="#e0e0e0", font=("Arial", 10, "bold"),
            width=40).pack(fill=tk.X, pady=(0, 5))
    
    # Frame de scroll para os perfis
    canvas = tk.Canvas(list_frame, bg="#f0f0f0", highlightthickness=0)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
    profiles_frame = tk.Frame(canvas, bg="#f0f0f0")
    
    profiles_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=profiles_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Criar perfis padrão
    perfis_padrao = [
        ("tt it", 30),
        ("jag,ward,p90", 16),
        ("ash", 18),
    ]
    
    # Adicionar perfis padrão
    for nome, intensidade in perfis_padrao:
        perfil = Perfil(nome, intensidade)
        profiles.append(perfil)
        adicionar_perfil_na_interface(perfil, profiles_frame)
    
    # Botão para adicionar novo perfil
    add_button = tk.Button(main_frame, text="Adicionar Novo Perfil", command=criar_novo_perfil,
                          bg="#4a6ea9", fg="white", width=20)
    add_button.pack(pady=10)
    
    # Botão para iniciar/parar
    start_button = tk.Button(main_frame, text="Iniciar", command=start_script, 
                            bg="#4CAF50", fg="white", width=15, height=2)
    start_button.pack(pady=15)
    
    # Instruções de uso
    instruction_text = "Selecione um perfil, mantenha o botão esquerdo do mouse\npressionado para ativar o assistente\n\nPressione F9 para iniciar/parar o programa"
    tk.Label(main_frame, text=instruction_text, 
             bg="#f0f0f0", font=("Arial", 8), justify=tk.CENTER).pack(pady=5)
    
    # Registra tecla F9 usando a biblioteca keyboard
    keyboard.on_press_key('f9', lambda _: toggle_script_state())
    
    # Configura fechamento da janela
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

# Inicia a interface
if __name__ == "__main__":
    try:
        show_ui()
    except Exception as e:
        print(f"Erro ao iniciar a aplicação: {e}")
