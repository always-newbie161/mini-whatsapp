import socket
import threading

PORT = 9999
SERVER_IP = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER_IP, PORT)
DISCONNECT_MSG = '!EXIT'
clients_dict = {} # will store name and socket objet

# making a server socket for devices in the same network to connect
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)


def send_all(name, msg):
    for clients in clients_dict:
        if clients != name:
            clients_dict[clients].send(msg.encode())


def handle_client(name, conn, addr):
    print(f"[NEW CONNECTION] {addr} connected, Name: {name}")
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
    send_all(name,f"[NEW CONNECTION] Name: {name}")

    while True:
        msg = conn.recv(1024).decode()
        if len(msg)!=0:
            if msg == DISCONNECT_MSG:
                print(f"[USER DISCONNECTED] {addr} disconnected, Name: {name}")
                send_all(name, f"[USER DISCONNECTED] Name: {name}")
                clients_dict.pop(name)
                break
            else:
                print(f"{msg}")
                send_all(name, msg)
        else:
            print(f"reading msg even without user input!")
    conn.close()


def start():
    server.listen()
    print(f"Server is listening on {SERVER_IP}")
    while True:
        # we wait on below line for a new conncetion
        conn, addr = server.accept()
        name = conn.recv(1024).decode()
        # when a new conncetion occur, we store and socket object correponding name
        clients_dict[name] = conn
        thread = threading.Thread(target=handle_client, args=(name, conn, addr), daemon=True)
        thread.start()


print("[STARTING] server is staring...")
start()
