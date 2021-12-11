import socket
import threading
import os
import glob
import tqdm, time
from cryptography.fernet import Fernet

PORT = 9999
# SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_IP = 'localhost'
ADDR = (SERVER_IP, PORT)
DISCONNECT_MSG = '!EXIT'
FILE_MSG = 'FILE'
UPLOAD_MSG = 'UPLOAD'
DOWNLOAD_MSG = 'DOWNLOAD'
LIST_MSG = 'LIST'
PVT_MSG = 'PVT'
BUF_SIZE = 1024
clients_dict = {}  # will store name and socket object

# making a server socket for devices in the same network to connect
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)


def gen_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    return key


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

        if len(msg) != 0:
            if msg == DISCONNECT_MSG:
                print(f"[USER DISCONNECTED] {addr} disconnected, Name: {name}")
                send_all(name, f"[USER DISCONNECTED] Name: {name}")
                clients_dict.pop(name)
                break
            elif msg.startswith(UPLOAD_MSG):
                _, filename, filesize = msg.split(' ')

                # check if a file with same name alredy exists
                filename_loc = "server/" + filename
                file_exists = os.path.exists(filename_loc)

                if file_exists:
                    # if another file with same name already exist in the server client can't rewrite it
                    send_client(name, "[SERVER REJECT] UPLOAD 0, another file with same name exists")
                    print(f"[SERVER REJECT] UPLOAD from {name} rejected, {filename} already exists")
                else:
                    print("Filename:", filename)
                    print("Filesize:", filesize, "bytes")

                    send_client(name, "[SERVER GRANT] UPLOAD 1")

                    NUM_CHUNKS = int(filesize) // BUF_SIZE + 1
                    packet_size = conn.recv(BUF_SIZE).decode()
                    progress = tqdm.tqdm(range(int(filesize)), desc=f"Recieving {filename}", unit="B", unit_scale=True,
                                        unit_divisor=1024)
                    with open(filename_loc, "wb") as file:
                        for _ in range(NUM_CHUNKS):
                            chunk = conn.recv(int(packet_size)).decode()
                            if not chunk:
                                break
                            key, encr_msg = chunk.split('#')
                            f = Fernet(key.encode())
                            decr_chunk = f.decrypt(encr_msg.encode())
                            file.write(decr_chunk)
                            # Update the progress bar
                            progress.update(len(decr_chunk))
                        progress.close()

                    print(f"File {filename} Received from {name}")
                    send_client(name, f"[SERVER UPDATE] Hi {name}, your file {filename} has been successfully uploaded")
                    send_all(name, f"[SERVER UPDATE] {name} has uploaded file {filename} to the server")

            elif msg.startswith(DOWNLOAD_MSG):
                _, filename = msg.split(' ')
                filename_loc = "server/" + filename
                print(f'[CLIENT REQUEST] DOWNLOAD {filename} from {addr[1]}, Name: {name}')
                file_exists = os.path.exists(filename_loc)

                if file_exists:
                    print(filename + " found")
                    
                    filesize = os.path.getsize(filename_loc)

                    send_client(name, f"[SERVER GRANT] DOWNLOAD {filesize} bytes")

                    NUM_CHUNKS = int(filesize) // BUF_SIZE + 1
                    progress = tqdm.tqdm(range(int(filesize)), desc=f"Sending {filename}", unit="B", unit_scale=True,
                                        unit_divisor=1024)
                    with open(filename_loc, "rb") as file:
                        for i in range(NUM_CHUNKS):
                            chunk = file.read(BUF_SIZE)
                            if not chunk:
                                break
                            key = gen_key()
                            f = Fernet(key)
                            encr_packet = '#'.join([key.decode(), f.encrypt(chunk).decode()]).encode()
                            if i == 0:
                                packet_size = len(encr_packet)
                                conn.send(str(packet_size).encode())
                                time.sleep(0.5)
                            send_allbytes(conn, encr_packet)
                            # Update the progress bar
                            progress.update(len(chunk))
                        progress.close()
                    print(f"File {filename} Downloaded to client {name}")
                else:
                    # file requested by user does not exist
                    send_client(name, f"[INVALID DOWNLOAD] file {filename} does not exist in the server {0}")              
                    print(f"[INVALID DOWNLOAD] {filename} Requested by client {name} does not exist")
                    
            elif msg.startswith(LIST_MSG):
                tokens = msg.split(' ')
                if len(tokens) == 1:
                    encoded_list = '\n'.join(glob.glob(r'server/*', recursive=True))
                    print(f'[CLIENT REQUEST] LIST ALL FILES  from {addr[1]}, Name: {name}')
                else:
                    re_pattern = tokens[1]
                    encoded_list = '\n'.join(glob.glob(r'server/' + re_pattern, recursive=True))
                    print(f'[CLIENT REQUEST] LIST {re_pattern} FILES  from {addr[1]}, Name: {name}')

                encoded_list = encoded_list if len(encoded_list) else 'No file found :('
                send_client(name, f"[SERVER GRANT] TO LIST all the requested files:\n{encoded_list}")

            elif msg.startswith(PVT_MSG):
                _,rec_name,pvt_msg = msg.split(' ')
                send_client(rec_name,pvt_msg)
                
            else:
                send_all(name, msg)
                
        else:
            print(f"[USER DISCONNECTED] {addr} disconnected, Name: {name}")
            send_all(name, f"[USER DISCONNECTED] Name: {name}")
            clients_dict.pop(name)
            break

    conn.close()


def start():
    server.listen()
    print(f"Server is listening on {SERVER_IP}")
    while True:
        # we wait on below line for a new connection
        conn, addr = server.accept()
        name = conn.recv(BUF_SIZE).decode()
        # when a new connection occur, we store and socket object's corresponding name
        # but first check if name already exists and if it does then ask client alternate name
        if name in clients_dict:
            # ask client ti retry with a different useranme
            print("[ACCESS DENIED] New Client tried to login with a name already is use")
            denied_msg = 'ACCESS DENIED, Username already in use'
            send_allbytes(conn, denied_msg.encode())
            conn.close()

        else:
            accepted_msg = 'ACCESS GRANTED'
            send_allbytes(conn, accepted_msg.encode())
            clients_dict[name] = conn
            thread = threading.Thread(target=handle_client, args=(name, conn, addr), daemon=True)
            thread.start()


print("[STARTING] server is staring...")
start()
