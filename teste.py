import socket
import threading
import time

# Função para lidar com a recepção de mensagens
def handle_receive(client_socket, client_address):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            # Confirmação de recebimento da mensagem
            if client_socket in active_clients:
                client_socket.send("ACK".encode())
            # Propaga a mensagem para todos os outros clientes online
            for peer_socket in active_clients:
                if peer_socket != client_socket:
                    peer_socket.send(message.encode())
        except ConnectionResetError:
            break
    # Remove o socket do cliente quando a conexão é fechada
    if client_socket in active_clients:
        active_clients.remove(client_socket)
    print(f"Conexão com {client_address} encerrada.")
    client_socket.close()

# Função para lidar com os batimentos cardíacos
def handle_heartbeats():
    while True:
        time.sleep(5)  # Intervalo de verificação dos batimentos cardíacos
        now = time.time()
        for client_socket in list(active_clients):
            last_heartbeat_time = heartbeat_timestamps.get(client_socket, 0)
            if now - last_heartbeat_time > 10:  # Tempo limite para considerar offline
                active_clients.remove(client_socket)
                print(f"Cliente offline: {client_socket.getpeername()}")

# Inicialização do servidor
HOST = '127.0.0.1'
PORT = 5555
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

active_clients = set()  # Conjunto de clientes online
heartbeat_timestamps = {}  # Dicionário para manter o timestamp dos últimos batimentos cardíacos

print("Servidor P2P iniciado.")

# Inicia uma nova thread para lidar com os batimentos cardíacos
threading.Thread(target=handle_heartbeats).start()

# Aguarda conexões de clientes
while True:
    client_socket, client_address = server_socket.accept()
    active_clients.add(client_socket)
    heartbeat_timestamps[client_socket] = time.time()  # Registra o timestamp do batimento cardíaco
    print(f"Conexão estabelecida com {client_address}.")
    # Inicia uma nova thread para lidar com a conexão do cliente
    threading.Thread(target=handle_receive, args=(client_socket, client_address)).start()
