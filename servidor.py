import socket
import threading
import json
import time
from datetime import datetime
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter.font import Font

# Configuração de logging compatível com Windows
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_server.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurar encoding para o console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

class NotificationServer:
    def __init__(self, host='servidor', port=80):
        self.host = host
        self.port = port
        self.clients = {}
        self.server_socket = None
        self.running = False
        self.auto_send_enabled = True  # Controle do envio automático
        self.auto_send_interval = 30  # Intervalo em segundos
        
        # MENSAGEM FIXA PADRÃO (link sempre enviado)
        self.default_message = "LinkParaRedirecionamento.com.br"
        
    def start_server(self):
        """Inicia o servidor"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            
            logging.info(f"Servidor iniciado em {self.host}:{self.port}")
            
            # Iniciar thread de envio automático
            self.start_auto_send_thread()
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    logging.info(f"Cliente conectado: {address}")
                    
                    # Enviar mensagem imediatamente quando cliente conectar
                    self.send_immediate_notification(client_socket)
                    
                    # Criar thread para gerenciar cliente
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logging.error(f"Erro ao aceitar conexão: {e}")
                        
        except Exception as e:
            logging.error(f"Erro ao iniciar servidor: {e}")
    
    def start_auto_send_thread(self):
        """Inicia a thread de envio automático"""
        def auto_send_loop():
            logging.info(f"ߔ䠌oop automático iniciado - enviando a cada {self.auto_send_interval} segundos")
            
            while self.running:
                try:
                    # Aguardar o intervalo
                    for _ in range(self.auto_send_interval):
                        if not self.running:
                            break
                        time.sleep(1)
                    
                    # Enviar apenas se estiver habilitado e houver clientes
                    if self.auto_send_enabled and self.running and self.clients:
                        count = self.send_to_all_clients()
                        if count > 0:
                            logging.info(f"ߤ栅nvio automático realizado para {count} cliente(s)")
                    
                except Exception as e:
                    logging.error(f"Erro no loop automático: {e}")
                    time.sleep(5)  # Aguardar antes de tentar novamente
        
        auto_thread = threading.Thread(target=auto_send_loop)
        auto_thread.daemon = True
        auto_thread.start()
    
    def send_notification(self, message=None, title=None, notification_type='info'):
        """Envia notificação personalizada para todos os clientes conectados"""
        if not self.clients:
            logging.info("Nenhum cliente conectado para enviar notificação")
            return 0
            
        # Sempre inclui o link padrão, destacado no final da mensagem
        if message and message != self.default_message:
            full_message = f"{message}\n\n\n\n\n\n\n\n\nLINK PARA O ACESSO AO SITE ABAIXO\n{self.default_message}"
        else:
            full_message = f"ߔ砻self.default_message}"
        
        notification = {
            'type': 'notification',
            'title': title or 'NOTIFICAÇÕES DE INCONSISTÊNCIAS DA FRENTE DE CAIXA',
            'message': full_message,
            'notification_type': notification_type,
            'timestamp': time.time(),
            'link': self.default_message
        }
        
        success_count = 0
        clients_to_remove = []
        
        for client_id, client_info in self.clients.items():
            try:
                client_socket = client_info['socket']
                client_socket.send(json.dumps(notification).encode('utf-8'))
                success_count += 1
                logging.info(f"Notificação enviada para {client_id}")
            except Exception as e:
                logging.error(f"Erro ao enviar para {client_id}: {e}")
                clients_to_remove.append(client_id)
        
        # Remover clientes com erro
        for client_id in clients_to_remove:
            if client_id in self.clients:
                del self.clients[client_id]
        
        logging.info(f"Notificação enviada para {success_count} cliente(s)")
        return success_count
    
    def send_to_all_clients(self):
        """Envia notificação padrão para todos os clientes conectados"""
        return self.send_notification(
            message=None,
            title='ACESSE O SITE PARA VERIFICAR AS INCONSISTÊNCIAS',
            notification_type='warning'
        )
    
    def send_immediate_notification(self, client_socket):
        """Envia notificação imediatamente após conexão"""
        try:
            notification = {
                'type': 'notification',
                'title': 'LEMBRETE IMPORTANTE',
                'message': f"\n\n\n\n\n\n\n\n\n\n\n\n\nACESSE O LINK ABAIXO PARA VERIFICAR AS INCONSISTÊNCIAS\n{self.default_message}",
                'notification_type': 'warning',
                'timestamp': time.time(),
                'link': self.default_message
            }
            client_socket.send(json.dumps(notification).encode('utf-8'))
            logging.info("Notificação enviada imediatamente")
        except Exception as e:
            logging.error(f"Erro ao enviar notificação imediata: {e}")
    
    def handle_client(self, client_socket, address):
        """Gerencia conexão do cliente"""
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = {
            'socket': client_socket,
            'address': address,
            'connected_at': datetime.now()
        }
        
        try:
            while self.running:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                        
                    message = json.loads(data)
                    
                    if message.get('type') == 'heartbeat':
                        response = {'type': 'heartbeat_ack', 'timestamp': time.time()}
                        client_socket.send(json.dumps(response).encode('utf-8'))
                        
                    elif message.get('type') == 'notification_response':
                        logging.info(f"Cliente {client_id} respondeu: {message.get('action')}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"Erro com cliente {client_id}: {e}")
                    break
                    
        except Exception as e:
            logging.error(f"Erro na conexão com cliente {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            client_socket.close()
            logging.info(f"Cliente {client_id} desconectado")
    
    def toggle_auto_send(self):
        """Alterna o envio automático"""
        self.auto_send_enabled = not self.auto_send_enabled
        status = "habilitado" if self.auto_send_enabled else "desabilitado"
        logging.info(f"ߔ䠅nvio automático {status}")
        return self.auto_send_enabled
    
    def set_auto_send_interval(self, interval):
        """Define o intervalo de envio automático"""
        if interval >= 5:  # Mínimo de 5 segundos
            self.auto_send_interval = interval
            logging.info(f"⏰ Intervalo de envio automático alterado para {interval} segundos")
            return True
        return False
    
    def get_client_count(self):
        """Retorna o número de clientes conectados"""
        return len(self.clients)
    
    def stop_server(self):
        """Para o servidor"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logging.info("Servidor parado")

class NotificationGUI:
    def __init__(self, server):
        self.server = server
        self.root = tk.Tk()
        self.root.title("⚡ Servidor de Notificações - Com Loop Automático")
        self.root.geometry("950x800")
        self.root.configure(bg="#1e1e2e")
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()
        
        # Variáveis
        self.server_running = tk.BooleanVar()
        self.auto_send_status = tk.BooleanVar(value=True)
        self.next_send_time = None
        
        self.setup_ui()
        self.start_server_thread()
        self.start_update_thread()
        
        # Protocolo para fechar janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def configure_styles(self):
        """Configura estilos modernos para a interface"""
        # Configurar cores
        bg_color = "#1e1e2e"
        card_color = "#313244"
        accent_color = "#89b4fa"
        text_color = "#cdd6f4"
        success_color = "#a6e3a1"
        warning_color = "#fab387"
        error_color = "#f38ba8"
        
        self.style.configure("Title.TLabel", 
                           background=bg_color, 
                           foreground=accent_color, 
                           font=("Segoe UI", 16, "bold"))
        
        self.style.configure("Card.TFrame", 
                           background=card_color, 
                           relief="solid", 
                           borderwidth=1)
        
        self.style.configure("Modern.TButton",
                           font=("Segoe UI", 10, "bold"),
                           padding=(10, 8))
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Título principal
        title_frame = tk.Frame(self.root, bg="#1e1e2e")
        title_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = tk.Label(title_frame, 
                              text="⚡ SERVIDOR DE NOTIFICAÇÕES - COM LOOP AUTOMÁTICO",
                              font=("Segoe UI", 18, "bold"),
                              bg="#1e1e2e", 
                              fg="#fab387")
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Sistema de Controle PDV - Envios automáticos a cada 30 segundos + envios manuais",
                                 font=("Segoe UI", 10),
                                 bg="#1e1e2e",
                                 fg="#a6adc8")
        subtitle_label.pack()
        
        # Frame de status
        self.setup_status_frame()
        
        # Frame de controle automático
        self.setup_auto_control_frame()
        
        # Frame de envio de mensagens
        self.setup_message_frame()
        
        # Frame de logs
        self.setup_log_frame()
        
        # Frame de controles
        self.setup_control_frame()
    
    def setup_status_frame(self):
        """Configura o frame de status do servidor"""
        status_frame = ttk.LabelFrame(self.root, text=" ߓꠓTATUS DO SERVIDOR ", padding=15)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        # Status do servidor
        status_info_frame = tk.Frame(status_frame, bg="#313244")
        status_info_frame.pack(fill="x")
        
        # Indicador visual de status
        self.status_indicator = tk.Label(status_info_frame,
                                        text="●",
                                        font=("Segoe UI", 20),
                                        bg="#313244",
                                        fg="#f38ba8")
        self.status_indicator.pack(side="left")
        
        self.status_label = tk.Label(status_info_frame,
                                    text="Servidor: Parado",
                                    font=("Segoe UI", 12, "bold"),
                                    bg="#313244",
                                    fg="#cdd6f4")
        self.status_label.pack(side="left", padx=(5, 0))
        
        # Contador de clientes
        self.clients_label = tk.Label(status_info_frame,
                                     text="ߑ堃lientes Conectados: 0",
                                     font=("Segoe UI", 10),
                                     bg="#313244",
                                     fg="#a6adc8")
        self.clients_label.pack(side="right")
        
        # Informações do servidor
        info_frame = tk.Frame(status_frame, bg="#313244")
        info_frame.pack(fill="x", pady=(10, 0))
        
        server_info = tk.Label(info_frame,
                              text=f"ߌࠅndereço: {self.server.host}:{self.server.port}",
                              font=("Segoe UI", 9),
                              bg="#313244",
                              fg="#a6adc8")
        server_info.pack(side="left")
        
        auto_info = tk.Label(info_frame,
                            text="ߔ䠅nvio automático ativo",
                            font=("Segoe UI", 9),
                            bg="#313244",
                            fg="#a6e3a1")
        auto_info.pack(side="right")
    
    def setup_auto_control_frame(self):
        """Configura o frame de controle automático"""
        auto_frame = ttk.LabelFrame(self.root, text=" ߤ栃ONTROLE AUTOMÁTICO ", padding=15)
        auto_frame.pack(fill="x", padx=20, pady=10)
        
        # Status do envio automático
        status_frame = tk.Frame(auto_frame, bg="#313244")
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.auto_indicator = tk.Label(status_frame,
                                      text="●",
                                      font=("Segoe UI", 16),
                                      bg="#313244",
                                      fg="#a6e3a1")
        self.auto_indicator.pack(side="left")
        
        self.auto_status_label = tk.Label(status_frame,
                                         text="Envio Automático: ATIVO",
                                         font=("Segoe UI", 11, "bold"),
                                         bg="#313244",
                                         fg="#cdd6f4")
        self.auto_status_label.pack(side="left", padx=(5, 0))
        
        # Próximo envio
        self.next_send_label = tk.Label(status_frame,
                                       text="⏰ Próximo envio em: --",
                                       font=("Segoe UI", 10),
                                       bg="#313244",
                                       fg="#a6adc8")
        self.next_send_label.pack(side="right")
        
        # Controles
        controls_frame = tk.Frame(auto_frame, bg="#313244")
        controls_frame.pack(fill="x")
        
        # Intervalo
        interval_label = tk.Label(controls_frame,
                                 text="⏱️ Intervalo (segundos):",
                                 font=("Segoe UI", 10),
                                 bg="#313244",
                                 fg="#cdd6f4")
        interval_label.pack(side="left")
        
        self.interval_var = tk.StringVar(value="30")
        interval_entry = tk.Entry(controls_frame,
                                 textvariable=self.interval_var,
                                 width=8,
                                 font=("Segoe UI", 10),
                                 bg="#45475a",
                                 fg="#cdd6f4",
                                 relief="flat")
        interval_entry.pack(side="left", padx=(5, 10))
        
        # Botão aplicar intervalo
        apply_button = tk.Button(controls_frame,
                                text="✓ Aplicar",
                                font=("Segoe UI", 9),
                                bg="#89b4fa",
                                fg="#1e1e2e",
                                relief="flat",
                                padx=10,
                                command=self.apply_interval)
        apply_button.pack(side="left", padx=(0, 15))
        
        # Botão toggle automático
        self.toggle_button = tk.Button(controls_frame,
                                      text="⏸️ PAUSAR AUTOMÁTICO",
                                      font=("Segoe UI", 10, "bold"),
                                      bg="#fab387",
                                      fg="#1e1e2e",
                                      activebackground="#f9e2af",
                                      relief="flat",
                                      padx=15,
                                      command=self.toggle_auto_send)
        self.toggle_button.pack(side="right")
    
    def setup_message_frame(self):
        """Configura o frame de envio de mensagens"""
        message_frame = ttk.LabelFrame(self.root, text=" ߒ젅NVIAR NOTIFICAÇÃO MANUAL ", padding=15)
        message_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Campo de título
        title_label = tk.Label(message_frame, 
                              text="ߓ�ítulo da Notificação:",
                              font=("Segoe UI", 10, "bold"),
                              bg="#313244",
                              fg="#cdd6f4")
        title_label.pack(anchor="w")
        
        self.title_entry = tk.Entry(message_frame,
                                   font=("Segoe UI", 10),
                                   bg="#45475a",
                                   fg="#cdd6f4",
                                   insertbackground="#cdd6f4",
                                   relief="flat",
                                   bd=5)
        self.title_entry.pack(fill="x", pady=(5, 15))
        self.title_entry.insert(0, "NOTIFICAÇÕES DE INCONSISTÊNCIAS DA FRENTE DE CAIXA")
        
        # Campo de mensagem
        message_label = tk.Label(message_frame,
                                text="ߒ�ensagem:",
                                font=("Segoe UI", 10, "bold"),
                                bg="#313244",
                                fg="#cdd6f4")
        message_label.pack(anchor="w")
        
        self.message_text = scrolledtext.ScrolledText(message_frame,
                                                     height=4,
                                                     font=("Segoe UI", 10),
                                                     bg="#45475a",
                                                     fg="#cdd6f4",
                                                     insertbackground="#cdd6f4",
                                                     relief="flat",
                                                     bd=5)
        self.message_text.pack(fill="both", expand=True, pady=(5, 15))
        
        # Tipo de notificação
        type_frame = tk.Frame(message_frame, bg="#313244")
        type_frame.pack(fill="x", pady=(0, 15))
        
        type_label = tk.Label(type_frame,
                             text="ߏ篸ipo:",
                             font=("Segoe UI", 10, "bold"),
                             bg="#313244",
                             fg="#cdd6f4")
        type_label.pack(side="left")
        
        self.notification_type = ttk.Combobox(type_frame,
                                            values=["info", "warning", "error", "success"],
                                            state="readonly",
                                            width=12)
        self.notification_type.pack(side="left", padx=(10, 0))
        self.notification_type.set("info")
        
        # Botões de envio
        buttons_frame = tk.Frame(message_frame, bg="#313244")
        buttons_frame.pack(fill="x")
        
        send_button = tk.Button(buttons_frame,
                               text="ߓ䠅NVIAR NOTIFICAÇÃO",
                               font=("Segoe UI", 11, "bold"),
                               bg="#89b4fa",
                               fg="#1e1e2e",
                               activebackground="#74c7ec",
                               relief="flat",
                               padx=20,
                               pady=8,
                               command=self.send_custom_notification)
        send_button.pack(side="left")
        
        send_default_button = tk.Button(buttons_frame,
                                       text="⚡ ENVIAR LINK AGORA",
                                       font=("Segoe UI", 11, "bold"),
                                       bg="#fab387",
                                       fg="#1e1e2e",
                                       activebackground="#f9e2af",
                                       relief="flat",
                                       padx=20,
                                       pady=8,
                                       command=self.send_default_notification)
        send_default_button.pack(side="right")
    
    def setup_log_frame(self):
        """Configura o frame de logs"""
        log_frame = ttk.LabelFrame(self.root, text=" ߓ렌OGS DE ATIVIDADE ", padding=10)
        log_frame.pack(fill="x", padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=6,
                                                 font=("Consolas", 9),
                                                 bg="#181825",
                                                 fg="#a6adc8",
                                                 insertbackground="#a6adc8",
                                                 relief="flat")
        self.log_text.pack(fill="both", expand=True)
        
        # Adicionar handler personalizado para logs
        self.setup_log_handler()
    
    def setup_control_frame(self):
        """Configura o frame de controles"""
        control_frame = ttk.LabelFrame(self.root, text=" ⚙️ CONTROLES ", padding=15)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # Frame para botões de ação
        action_frame = tk.Frame(control_frame, bg="#313244")
        action_frame.pack(fill="x")
        
        # Botão para envio manual imediato
        manual_button = tk.Button(action_frame,
                                 text="ߚࠅNVIAR AGORA",
                                 font=("Segoe UI", 12, "bold"),
                                 bg="#a6e3a1",
                                 fg="#1e1e2e",
                                 activebackground="#94e2d5",
                                 relief="flat",
                                 padx=25,
                                 pady=8,
                                 command=self.send_immediate)
        manual_button.pack(side="left")
        
        # Botão de parar servidor
        stop_button = tk.Button(action_frame,
                               text="ߛ᠐ARAR SERVIDOR",
                               font=("Segoe UI", 12, "bold"),
                               bg="#f38ba8",
                               fg="#1e1e2e",
                               activebackground="#eba0ac",
                               relief="flat",
                               padx=25,
                               pady=8,
                               command=self.stop_server)
        stop_button.pack(side="right")
    
    def setup_log_handler(self):
        """Configura handler personalizado para mostrar logs na interface"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                # Limitar número de linhas
                lines = self.text_widget.get("1.0", tk.END).count('\n')
                if lines > 100:
                    self.text_widget.delete("1.0", "2.0")
        
        # Adicionar handler GUI ao logger
        gui_handler = GUILogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
    
    def start_server_thread(self):
        """Inicia o servidor em uma thread separada"""
        server_thread = threading.Thread(target=self.server.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Inicializar contagem regressiva
        self.next_send_time = time.time() + self.server.auto_send_interval
    
    def start_update_thread(self):
        """Inicia thread para atualizar interface periodicamente"""
        def update_interface():
            while True:
                try:
                    self.root.after(0, self.update_status)
                    time.sleep(1)
                except:
                    break
        
        update_thread = threading.Thread(target=update_interface)
        update_thread.daemon = True
        update_thread.start()
    
    def update_status(self):
        """Atualiza o status na interface"""
        # Status do servidor
        if self.server.running:
            self.status_indicator.config(fg="#a6e3a1")  # Verde
            self.status_label.config(text="Servidor: Online")
        else:
            self.status_indicator.config(fg="#f38ba8")  # Vermelho
            self.status_label.config(text="Servidor: Parado")
        
        # Atualizar contador de clientes
        client_count = self.server.get_client_count()
        self.clients_label.config(text=f"ߑ堃lientes Conectados: {client_count}")
        
        # Status do envio automático
        if self.server.auto_send_enabled:
            self.auto_indicator.config(fg="#a6e3a1")  # Verde
            self.auto_status_label.config(text="Envio Automático: ATIVO")
            self.toggle_button.config(text="⏸️ PAUSAR AUTOMÁTICO", bg="#fab387")
            
            # Atualizar contagem regressiva
            if self.next_send_time:
                remaining = max(0, int(self.next_send_time - time.time()))
                if remaining <= 0:
                    self.next_send_time = time.time() + self.server.auto_send_interval
                    remaining = self.server.auto_send_interval
                
                minutes = remaining // 60
                seconds = remaining % 60
                self.next_send_label.config(text=f"⏰ Próximo envio em: {minutes:02d}:{seconds:02d}")
        else:
            self.auto_indicator.config(fg="#f38ba8")  # Vermelho
            self.auto_status_label.config(text="Envio Automático: PAUSADO")
            self.toggle_button.config(text="▶️ ATIVAR AUTOMÁTICO", bg="#a6e3a1")
            self.next_send_label.config(text="⏰ Envio automático pausado")
    
    def toggle_auto_send(self):
        """Alterna o envio automático"""
        enabled = self.server.toggle_auto_send()
        if enabled:
            self.next_send_time = time.time() + self.server.auto_send_interval
            messagebox.showinfo("Ativado", "ߔ䠅nvio automático ativado!")
        else:
            messagebox.showinfo("Pausado", "⏸️ Envio automático pausado!")
    
    def apply_interval(self):
        """Aplica novo intervalo de envio automático"""
        try:
            interval = int(self.interval_var.get())
            if self.server.set_auto_send_interval(interval):
                self.next_send_time = time.time() + interval
                messagebox.showinfo("Sucesso", f"⏰ Intervalo alterado para {interval} segundos!")
            else:
                messagebox.showwarning("Erro", "❌ Intervalo mínimo é 5 segundos!")
                self.interval_var.set(str(self.server.auto_send_interval))
        except ValueError:
            messagebox.showerror("Erro", "❌ Digite um número válido!")
            self.interval_var.set(str(self.server.auto_send_interval))
    
    def send_immediate(self):
        """Envia notificação imediatamente para todos os clientes"""
        try:
            count = self.server.send_to_all_clients()
            
            if count > 0:
                messagebox.showinfo("Enviado", f"⚡ Notificação enviada para {count} cliente(s)!")
                logging.info(f"ߚࠅnvio manual para {count} cliente(s)")
            else:
                messagebox.showwarning("Aviso", "❌ Nenhum cliente conectado!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao enviar notificação: {str(e)}")
    
    def send_custom_notification(self):
        """Envia notificação personalizada"""
        title = self.title_entry.get().strip()
        message = self.message_text.get("1.0", tk.END).strip()
        notification_type = self.notification_type.get()
        
        if not message:
            messagebox.showwarning("Aviso", "Por favor, digite uma mensagem!")
            return
        
        try:
            count = self.server.send_notification(
                message=message,
                title=title or None,
                notification_type=notification_type
            )
            
            if count > 0:
                messagebox.showinfo("Sucesso", f"✅ Notificação enviada para {count} cliente(s)!")
            else:
                messagebox.showwarning("Aviso", "❌ Nenhum cliente conectado!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao enviar notificação: {str(e)}")
    
    def send_default_notification(self):
        """Envia notificação padrão (apenas link)"""
        try:
            count = self.server.send_to_all_clients()
            
            if count > 0:
                messagebox.showinfo("Sucesso", f"⚡ Link enviado para {count} cliente(s)!")
            else:
                messagebox.showwarning("Aviso", "❌ Nenhum cliente conectado!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao enviar link: {str(e)}")
    
    def stop_server(self):
        """Para o servidor"""
        if messagebox.askyesno("Confirmação", "Tem certeza que deseja parar o servidor?"):
            self.server.stop_server()
            messagebox.showinfo("Info", "Servidor parado com sucesso!")
    
    def on_closing(self):
        """Chamado quando a janela é fechada"""
        if messagebox.askyesno("Sair", "Deseja realmente fechar o servidor?"):
            self.server.stop_server()
            self.root.destroy()
    
    def run(self):
        """Executa a interface gráfica"""
        self.root.mainloop()

def main():
    print("⚡ Iniciando Servidor de Notificações - Com Loop Automático...")
    
    server = NotificationServer()
    gui = NotificationGUI(server)
    
    try:
        gui.run()
    except KeyboardInterrupt:
        server.stop_server()
        print("\nߑ렓ervidor finalizado.")

if __name__ == "__main__":
    main()
