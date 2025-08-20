📢 Sistema de Notificações em Rede (Servidor & Cliente)
Este projeto implementa um sistema de notificações em tempo real entre um servidor e múltiplos clientes utilizando sockets TCP e uma interface gráfica em Tkinter.

O sistema foi desenvolvido para cenários de monitoramento, alertas e comunicação em redes internas (LAN).

🚀 Funcionalidades
🔹 Servidor
Interface gráfica moderna (Tkinter + ttk).
Envio automático de notificações em intervalo configurável.
Envio manual de mensagens personalizadas ou link fixo.
Controle para pausar/retomar o envio automático.
Log de atividade em arquivo (notification_server.log) e na própria interface.
Contador de clientes conectados em tempo real.
🔹 Cliente
Conecta ao servidor e recebe notificações automaticamente.
Exibe mensagens em janelas pop-up personalizadas.
Suporte a links clicáveis (abre navegador automaticamente).
Responde ao servidor com ações (OK, Dispensar, Auto Close).
Envio de heartbeat a cada 30s para manter conexão ativa.
Funciona em background, minimizado, com opção de sair pelo menu.
▶️ Como Executar
🔹 1. Inicie o Servidor
No terminal, execute:

python server.py
O servidor será iniciado no host/porta configurado (10.110.96.44:80 por padrão).

🔹 2. Inicie o Cliente
Em outra máquina (ou na mesma):

python client.py
O cliente se conectará ao servidor e ficará em background, recebendo notificações.

📝 Logs
Servidor: notification_server.log
Cliente: notification_client.log
Os logs armazenam eventos importantes como conexões, erros e notificações enviadas/recebidas.

⚠️ Observações
O sistema foi projetado para rodar em rede local (LAN).
É necessário liberar a porta 80 no firewall da máquina do servidor.
O IP do servidor deve ser ajustado em client.py e server.py caso seja diferente.
👨‍💻 Autor
Fabio Bessa Batista
📍 Belo Horizonte - MG
📧 bessafabio2000@gmail.com
📱 WhatsApp: (31) 99901-4717
🔗 LinkedIn
