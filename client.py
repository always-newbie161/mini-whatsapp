import datetime
import os
import re
import socket
import threading

PORT = 9999
flag = False
DISCONNECT_MSG = '!EXIT'
FILE_MSG = 'FILE'
UPLOAD_MSG = 'UPLOAD'
DOWNLOAD_MSG = 'DOWNLOAD'
LIST_MSG = 'LIST'
FILE_NAME = ''
FILE_SIZE = ''
BUF_SIZE = 1024
# SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_IP = 'localhost'
ADDR = (SERVER_IP, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
name = input("Enter your name: ")
print(f'[CONNECTING] To {SERVER_IP}:{PORT}')
client.connect(ADDR)
client.send(name.encode())
print(f"[JOINED SUCESSFULLY], Name: {name}")

def make_dirs():
    if not os.path.exists('client_files'):
        # directory to store files downloaded from server
        os.makedirs('client_files')

def send_allbytes(sock, data, flags=0):
    nbytes = sock.send(data, flags)
    if nbytes > 0:
        return send_allbytes(sock, data[nbytes:], flags)
    else:
        return None


def send_msg(msg):
    curr_time = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    msg_to_send = f"[{curr_time}] {name}: {msg}"
    send_allbytes(client, msg_to_send.encode())


def receive_msg():
    while True:
        global flag
        global FILE_NAME
        global FILE_SIZE
        message_recv = client.recv(BUF_SIZE).decode()
        print(message_recv)
        if 'UPLOAD' in message_recv:
            print("Uploading.....")

            NUM_CHUNKS = int(FILE_SIZE) // BUF_SIZE + 1
            with open(FILE_NAME, "rb") as file:
                for _ in range(NUM_CHUNKS):
                    chunk = file.read(BUF_SIZE)
                    if not chunk:
                        break
                    send_allbytes(client, chunk)

            flag = False

        elif 'DOWNLOAD' in message_recv:
            FILE_SIZE = re.findall(r'\d+', message_recv)[0]
            
            if int(FILE_SIZE) != 0:
                print("Downloading.....")
        
                NUM_CHUNKS = int(FILE_SIZE)//BUF_SIZE+1
                with open('client_files/'+FILE_NAME,"wb") as file:
                    for _ in range(NUM_CHUNKS):
                        chunk = client.recv(BUF_SIZE)
                        if not chunk:
                            break
                        file.write(chunk)

                print(f"File {FILE_NAME} Received")
                flag = False
            else:
                # requested file does not exist
                print("Download Failed")
                flag = False


thread = threading.Thread(target=receive_msg, daemon=True)
thread.start()


    

while True:
    message = input()

    if message == DISCONNECT_MSG:
        client.send(message.encode())
        client.close()
        break
    elif message.startswith(UPLOAD_MSG):

        _, FILE_NAME = message.split(' ')
        try:
            FILE_SIZE = os.path.getsize(FILE_NAME)
            message = f"{message} {FILE_SIZE}"
            client.send(message.encode())
            flag = True
            while (flag):
                continue
        except OSError:
            print("The file you tried to upload does not exist, Please check")

    elif message.startswith(DOWNLOAD_MSG):
        make_dirs()
        client.send(message.encode())
        _, FILE_NAME = message.split(' ')
        flag = True
        while (flag):
            continue

    elif message.startswith(LIST_MSG):
        client.send(message.encode())
    else:
        send_msg(message)
