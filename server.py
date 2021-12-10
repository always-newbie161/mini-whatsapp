import socket
import threading 
import os
                        # sendall vadacha choodali
PORT = 9999
SERVER_IP = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER_IP, PORT)
DISCONNECT_MSG = '!EXIT'
FILE_MSG = 'FILE'
UPLOAD_MSG = 'UPLOAD'
DOWNLOAD_MSG = 'DOWNLOAD'
BUF_SIZE = 1024
clients_dict = {} # will store name and socket objet

# making a server socket for devices in the same network to connect
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)


def send_all(name, msg):
    for clients in clients_dict:
        if clients != name:
            clients_dict[clients].send(msg.encode())

def send_client(name,msg):
    for clients in clients_dict:
        if clients == name:
            clients_dict[clients].send(msg.encode())



def handle_client(name, conn, addr):
    print(f"[NEW CONNECTION] {addr} connected, Name: {name}")
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
    send_all(name,f"[NEW CONNECTION] Name: {name}")

    while True:
        msg = conn.recv(BUF_SIZE).decode()
        if len(msg)!=0:
            if msg == DISCONNECT_MSG:
                print(f"[USER DISCONNECTED] {addr} disconnected, Name: {name}")
                send_all(name, f"[USER DISCONNECTED] Name: {name}")
                clients_dict.pop(name)
                break
            elif msg.startswith(UPLOAD_MSG):
                _,filename,filesize = msg.split(' ')
                print("Filename:", filename)
                print("Filesize:", filesize)

                send_client(name, "[SERVER GRANT] UPLOAD")
                filename_loc = "server/" + filename 
                
                NUM_CHUNKS = int(filesize)//BUF_SIZE+1
                with open(filename_loc,"wb") as file:
                    for _ in range(NUM_CHUNKS):
                        chunk = conn.recv(BUF_SIZE)    
                        if not chunk:
                            break
                        file.write(chunk)

                print(f"File {filename} Received from {name}")
                send_client(name, f"[SERVER UPDATE] Hi {name}, your file {filename} has been received")
                send_all(name, f"[SERVER UPDATE] {name} has uploaded file {filename} to the server")

            elif msg.startswith(DOWNLOAD_MSG):
                _,filename = msg.split(' ')
                filename_loc = "server/"+filename
                if os.path.exists(filename_loc):
                    print(filename + " found")               
                filesize = os.path.getsize(filename_loc)

                send_client(name, f"[SERVER GRANT] DOWNLOAD {filesize} bytes")

                NUM_CHUNKS = int(filesize)//BUF_SIZE+1
                with open(filename_loc,"rb") as file:
                    for _ in range(NUM_CHUNKS):
                        chunk = file.read(BUF_SIZE)
                        if not chunk:
                            break
                        conn.sendall(chunk)

                print(f"File {filename} Downloaded to client {name}")
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
        name = conn.recv(BUF_SIZE).decode()
        # when a new conncetion occur, we store and socket object correponding name
        clients_dict[name] = conn
        thread = threading.Thread(target=handle_client, args=(name, conn, addr), daemon=True)
        thread.start()


print("[STARTING] server is staring...")
start()
