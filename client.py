import socket
import threading
import datetime, os
import sys, time
import re

PORT = 9999
flag = False
DISCONNECT_MSG = '!EXIT'
FILE_MSG = 'FILE'
UPLOAD_MSG = 'UPLOAD'
DOWNLOAD_MSG = 'DOWNLOAD'
FILE_NAME = ''
FILE_SIZE = ''
BUF_SIZE = 1024
SERVER_IP = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER_IP, PORT)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
name = input("Enter your name: ")
print(f'[CONNECTING] To {SERVER_IP}:{PORT}')
client.connect(ADDR)
client.send(name.encode())
print(f"[JOINED SUCESSFULLY], Name: {name}")


def send_msg(msg):
    curr_time = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    msg_to_send = f"[{curr_time}] {name}: {msg}"
    client.send(msg_to_send.encode())

def receive_msg():
    while True:
        global flag
        global FILE_NAME
        global FILE_SIZE
        message_recv = client.recv(BUF_SIZE).decode()
        print(message_recv)
        if 'UPLOAD' in message_recv:
            print("Uploading.....")
            
            NUM_CHUNKS = int(FILE_SIZE)//BUF_SIZE+1
            with open(FILE_NAME,"rb") as file:
                for _ in range(NUM_CHUNKS):
                    chunk = file.read(BUF_SIZE)
                    if not chunk:
                        break
                    client.sendall(chunk)

            flag = False

        elif 'DOWNLOAD' in message_recv:
            FILE_SIZE = re.findall(r'\d+', message_recv)[0]
            print("Downloading.....")
            
            NUM_CHUNKS = int(FILE_SIZE)//BUF_SIZE+1
            with open(FILE_NAME,"wb") as file:
                for _ in range(NUM_CHUNKS):
                    chunk = client.recv(BUF_SIZE) 
                    if not chunk:
                        break
                    file.write(chunk)

            print(f"File {FILE_NAME} Received")
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
        FILE_SIZE = os.path.getsize(FILE_NAME)
        message = f"{message} {FILE_SIZE}"
        client.send(message.encode())
        flag = True
        while(flag):
            continue
    elif message.startswith(DOWNLOAD_MSG):
        client.send(message.encode())
        _, FILE_NAME = message.split(' ')
        FILE_NAME = 'server_'+FILE_NAME
        flag = True
        while(flag):
            continue

    else:
        send_msg(message)
    