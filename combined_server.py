import socket
import threading
import os
import http.server
import socketserver

# Render автоматически выдает порт через переменную среды PORT. Если ее нет, берем 55555
TCP_PORT = int(os.environ.get("PORT", 55555))
UDP_PORT = 9999

# --- НАСТРОЙКА ТЕКСТА (TCP) ---
tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server.bind(('0.0.0.0', TCP_PORT))
tcp_server.listen()

tcp_clients = []
nicknames = []

def broadcast_text(message, _client):
    for client in tcp_clients:
        if client != _client:
            try: 
                client.send(message)
            except: 
                remove_tcp_client(client)

def remove_tcp_client(client):
    if client in tcp_clients:
        idx = tcp_clients.index(client)
        tcp_clients.remove(client)
        client.close()
        nick = nicknames[idx]
        broadcast_text(f'[Сервер]: @{nick} покинул чат.'.encode('utf-8'), client)
        nicknames.remove(nick)

def handle_tcp(client):
    while True:
        try:
            msg = client.recv(1024)
            if not msg: 
                break
            broadcast_text(msg, client)
        except: 
            break
    remove_tcp_client(client)

def tcp_accept():
    print(f"Текстовый сервер запущен на порту {TCP_PORT}...")
    while True:
        try:
            client, addr = tcp_server.accept()
            client.send('NICK'.encode('utf-8'))
            nick = client.recv(1024).decode('utf-8')
            nicknames.append(nick)
            tcp_clients.append(client)
            broadcast_text(f'[Сервер]: @{nick} ворвался в чат!'.encode('utf-8'), client)
            threading.Thread(target=handle_tcp, args=(client,), daemon=True).start()
        except:
            pass

# --- НАСТРОЙКА ГОЛОСА (UDP) ---
udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(('0.0.0.0', UDP_PORT))
udp_clients = set()

def udp_handle():
    print(f"Голосовой server запущен на порту {UDP_PORT}...")
    while True:
        try:
            data, addr = udp_server.recvfrom(2048)
            if addr not in udp_clients:
                udp_clients.add(addr)
            for client in udp_clients:
                if client != addr:
                    try: 
                        udp_server.sendto(data, client)
                    except: 
                        udp_clients.remove(client)
        except: 
            pass

# --- ЗАГЛУШКА ДЛЯ RENDER (HTTP) ---
def run_dummy_http():
    # Создаем простейший веб-ответ, чтобы Render не ругался
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Server is running!")

    # Запускаем его на случайном свободном порту, просто для галочки
    with socketserver.TCPServer(("", 8080), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=tcp_accept, daemon=True).start()
    threading.Thread(target=udp_handle, daemon=True).start()
    threading.Thread(target=run_dummy_http, daemon=True).start()
    
    try:
        while True: 
            pass
    except KeyboardInterrupt:
        print("Сервер остановлен.")