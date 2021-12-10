import socket
import threading
import os
import glob

PORT = 9999
# SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_IP = 'localhost'
ADDR = (SERVER_IP, PORT)
DISCONNECT_MSG = '!EXIT'
FILE_MSG = 'FILE'
UPLOAD_MSG = 'UPLOAD'
DOWNLOAD_MSG = 'DOWNLOAD'
LIST_MSG = 'LIST'
BUF_SIZE = 1024
clients_dict = {}  # will store name and socket object

# making a server socket for devices in the same network to connect
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)


def send_allbytes(sock, data, flags=0):
    nbytes = sock.send(data, flags)
    if nbytes > 0:
        return send_allbytes(sock, data[nbytes:], flags)
    else:
        return None


def send_all(name, msg):
    for clients in clients_dict:
        if clients != name:
            send_allbytes(clients_dict[clients], msg.encode())


def send_client(name, msg):
    for clients in clients_dict:
        if clients == name:
            send_allbytes(clients_dict[clients], msg.encode())


def handle_client(name, conn, addr):
    print(f"[NEW CONNECTION] {addr} connected, Name: {name}")
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
    send_all(name, f"[NEW CONNECTION] Name: {name}")

    while True:
        msg = conn.recv(BUF_SIZE).decode()

        try:
            if msg == DISCONNECT_MSG:
                print(f"[USER DISCONNECTED] {addr} disconnected, Name: {name}")
                send_all(name, f"[USER DISCONNECTED] Name: {name}")
                clients_dict.pop(name)
                break
            elif msg.startswith(UPLOAD_MSG):
                _, filename, filesize = msg.split(' ')
                print("Filename:", filename)
                print("Filesize:", filesize, "bytes")

                send_client(name, "[SERVER GRANT] UPLOAD")
                filename_loc = "server/" + filename 
                
                NUM_CHUNKS = int(filesize) // BUF_SIZE + 1
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
                file_exists = os.path.exists(filename_loc)

                if file_exists:
                    print(filename + " found")
                    filesize = os.path.getsize(filename_loc)

                    send_client(name, f"[SERVER GRANT] DOWNLOAD {filesize} bytes")

                    NUM_CHUNKS = int(filesize) // BUF_SIZE + 1
                    with open(filename_loc,"rb") as file:
                        for _ in range(NUM_CHUNKS):
                            chunk = file.read(BUF_SIZE)
                            if not chunk:
                                break
                            send_allbytes(conn, chunk)
                    print(f"File {filename} Downloaded to client {name}")
                else:
                    # file requested by user does not exist
                    send_client(name, f"[INVALID DOWNLOAD] file {filename} does not exist in the server {0}")              
                    print(f"[INVALID DOWNLOAD] {filename} Requested by client {name} does not exist")
                
            elif msg.startswith(LIST_MSG):
                tokens = msg.split(' ')
                if len(tokens) == 1:
                    encoded_list = '\n'.join(glob.glob(r'server/*', recursive=True))
                    print('[CLIENT REQUEST] LIST ALL FILES')
                else:
                    re_pattern = tokens[1]
                    encoded_list = '\n'.join(glob.glob(r'server/' + re_pattern, recursive=True))
                    print(f'[CLIENT REQUEST] LIST {re_pattern} FILES')

                encoded_list = encoded_list if len(encoded_list) else 'No file found :('
                send_client(name, f"[SERVER GRANT] TO LIST all the requested files:\n{encoded_list}")
                
            else:
                print(f"{msg}")
                send_all(name, msg)
        except Exception:
            # when client shutdown conncetion improperly
            clients_dict.pop(name)
            conn.close
            #print(f"reading msg even without user input!")
    conn.close()


def start():
    server.listen()
    print(f"Server is listening on {SERVER_IP}")
    while True:
        # we wait on below line for a new connection
        conn, addr = server.accept()
        name = conn.recv(BUF_SIZE).decode()
        # when a new connection occur, we store and socket object's corresponding name
        clients_dict[name] = conn
        thread = threading.Thread(target=handle_client, args=(name, conn, addr), daemon=True)
        thread.start()


print("[STARTING] server is staring...")
start()
