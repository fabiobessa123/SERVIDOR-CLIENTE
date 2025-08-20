import socket
import threading
import json
import time
import tkinter as tk
from tkinter import messagebox
import logging
import sys
import os
import webbrowser

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_client.log'),
        logging.StreamHandler()
    ]
)

class NotificationClient:
    def __init__(self, server_host='10.110.96.44', server_port=80):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.root = None
        
    def connect_to_server(self):
        """Conecta ao servidor"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            self.running = True
            logging.info(f"Conectado ao servidor {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            logging.error(f"Erro ao conectar ao servidor: {e}")
            return False
    
    def listen_for_notifications(self):
        """Escuta notificações do servidor"""
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
#                if not data:
#                    break
                
                message = json.loads(data)
                
                if message.get('type') == 'notification':
                    # Processar notificação
                    self.show_notification(message)
                    
                elif message.get('type') == 'heartbeat_ack':
                    # Resposta ao heartbeat
                    pass
  
            except Exception as e:
                if self.running:
                    logging.error(f"Erro ao receber dados: {e}")
                break
        
        self.disconnect()
    
    def show_notification(self, notification):
        """Exibe notificação em pop-up"""
        try:
            title = notification.get('title', 'Notificação')
            message = notification.get('message', '')
            notification_type = notification.get('notification_type', 'info')
            
            # Criar janela de notificação
            self.create_notification_window(title, message, notification_type)
            
        except Exception as e:
            logging.error(f"Erro ao exibir notificação: {e}")
    
    def create_notification_window(self, title, message, notification_type):
        """Cria janela de notificação personalizada com link clicável"""
        try:
            # Criar nova janela
            notification_window = tk.Toplevel()
            notification_window.title(title)
            notification_window.geometry("800x600")
            notification_window.resizable(False, False)
            
            # Manter janela sempre no topo
            notification_window.attributes('-topmost', True)
            
            # Centralizar na tela
            notification_window.update_idletasks()
            x = (notification_window.winfo_screenwidth() // 2) - (800 // 2)
            y = (notification_window.winfo_screenheight() // 2) - (600 // 2)
            notification_window.geometry(f"800x600+{x}+{y}")
            
            # Cores baseadas no tipo
            colors = {
                'info': {'bg': '#e3f2fd', 'fg': '#1976d2'},
                'warning': {'bg': '#fff3e0', 'fg': '#f57c00'},
                'error': {'bg': '#ffebee', 'fg': '#d32f2f'}
            }
            
            color = colors.get(notification_type, colors['info'])
            notification_window.configure(bg=color['bg'])
            
            # Frame principal
            main_frame = tk.Frame(notification_window, bg=color['bg'])
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Título
            title_label = tk.Label(
                main_frame,
                text=title,
                font=('Arial', 14, 'bold'),
                fg=color['fg'],
                bg=color['bg']
            )
            title_label.pack(pady=(0, 10))
            
            # Função para abrir o link
            def open_link(event=None):
                webbrowser.open(message)  # Assume que message é a URL
            
            # Verificar se a mensagem é uma URL
            if isinstance(message, str) and message.startswith(('http://', 'https://')):
                # Texto explicativo
                tk.Label(
                    main_frame,
                    text="Verifique as inconsistências no sistema:",
                    font=('Arial', 11),
                    fg='#333333',
                    bg=color['bg'],
                    wraplength=400,
                    justify='left'
                ).pack(pady=(0, 5))
                
                # Criar label com estilo de link
                link_label = tk.Label(
                    main_frame,
                    text="Clique aqui para acessar o sistema",
                    font=('Arial', 11, 'underline'),
                    fg='blue',
                    bg=color['bg'],
                    cursor="hand2"
                )
                link_label.pack(pady=(0, 15))
                link_label.bind("<Button-1>", open_link)
                
                # Mostrar a URL reduzida
                shortened_url = message[:50] + '...' if len(message) > 50 else message
                tk.Label(
                    main_frame,
                    text=f"URL: {shortened_url}",
                    font=('Arial', 9),
                    fg='#666666',
                    bg=color['bg'],
                    wraplength=400,
                    justify='left'
                ).pack(pady=(0, 10))
            else:
                # Mensagem normal se não for URL
                message_label = tk.Label(
                    main_frame,
                    text=message,
                    font=('Arial', 11),
                    fg='#333333',
                    bg=color['bg'],
                    wraplength=400,
                    justify='left'
                )
                message_label.pack(pady=(0, 20))
            
            # Botões
            button_frame = tk.Frame(main_frame, bg=color['bg'])
            button_frame.pack(side='bottom')
            
            def on_ok():
                self.send_response('ok')
                notification_window.destroy()
            
            def on_dismiss():
                self.send_response('dismiss')
                notification_window.destroy()
            
            ok_button = tk.Button(
                button_frame,
                text="OK",
                command=on_ok,
                bg=color['fg'],
                fg='white',
                padx=20,
                pady=5
            )
            ok_button.pack(side='left', padx=(0, 10))
            
            dismiss_button = tk.Button(
                button_frame,
                text="Dispensar",
                command=on_dismiss,
                bg='#666666',
                fg='white',
                padx=20,
                pady=5
            )
            dismiss_button.pack(side='left')
            
            # Auto-close após 30 segundos
            def auto_close():
                if notification_window.winfo_exists():
                    self.send_response('auto_close')
                    notification_window.destroy()
            
            notification_window.after(6000000, auto_close)
            
            # Focar na janela
            notification_window.focus_force()
            
        except Exception as e:
            logging.error(f"Erro ao criar janela de notificação: {e}")
            # Fallback para messagebox padrão
            messagebox.showinfo(title, message)
    
    def send_response(self, action):
        """Envia resposta ao servidor"""
        try:
            response = {
                'type': 'notification_response',
                'action': action,
                'timestamp': time.time()
            }
            self.client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logging.error(f"Erro ao enviar resposta: {e}")
    
    def send_heartbeat(self):
        """Envia heartbeat para o servidor"""
        while self.running:
            try:
                if self.client_socket:
                    heartbeat = {
                        'type': 'heartbeat',
                        'timestamp': time.time()
                    }
                    self.client_socket.send(json.dumps(heartbeat).encode('utf-8'))
                time.sleep(30)  # Heartbeat a cada 30 segundos
            except Exception as e:
                if self.running:
                    logging.error(f"Erro ao enviar heartbeat: {e}")
                break
    
    def disconnect(self):
        """Desconecta do servidor"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        logging.info("Desconectado do servidor")
    
    def start_client(self):
        """Inicia o cliente"""
        # Conectar ao servidor
        if not self.connect_to_server():
            return False
        
        # Criar interface gráfica
        self.root = tk.Tk()
        self.root.title("Cliente de Notificações")
        self.root.geometry("300x150")
        
        # Ocultar janela principal (rodar em background)
        self.root.withdraw()
        
        # Iniciar thread para escutar notificações
        listen_thread = threading.Thread(target=self.listen_for_notifications)
        listen_thread.daemon = True
        listen_thread.start()
        
        # Iniciar thread para heartbeat
        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        # Criar ícone na system tray (opcional)
        self.create_system_tray_icon()
        
        # Iniciar loop da interface
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()
        
        return True
    
    def create_system_tray_icon(self):
        """Cria ícone na system tray"""
        try:
            # Criar menu de contexto
            def on_exit():
                self.running = False
                self.root.quit()
            
            # Criar menu simples na janela principal
            menu_frame = tk.Frame(self.root)
            menu_frame.pack(fill='both', expand=True)
            
            status_label = tk.Label(
                menu_frame,
                text="Cliente de Notificações\nExecutando em background",
                font=('Arial', 10),
                justify='center'
            )
            status_label.pack(pady=20)
            
            exit_button = tk.Button(
                menu_frame,
                text="Sair",
                command=on_exit,
                padx=20,
                pady=5
            )
            exit_button.pack()
            
        except Exception as e:
            logging.error(f"Erro ao criar system tray: {e}")

def main():
    # Configurar endereço do servidor
    server_host = '10.110.96.44'
    server_port = 80
    
    print(f"Conectando ao servidor {server_host}:{server_port}...")
    
    client = NotificationClient(server_host, server_port)
    
    if client.start_client():
        print("Cliente iniciado com sucesso! (Rodando em background)")
        print("Minimizado para a bandeja do sistema")
    else:
        print("Falha ao iniciar cliente")
        sys.exit(1)

if __name__ == "__main__":
    main()
