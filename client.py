import socket
import threading
import datetime

PORT = 9999
DISCONNECT_MSG = '!EXIT'
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
        message_recv = client.recv(1024).decode()
        print(message_recv)


thread = threading.Thread(target=receive_msg, daemon=True)
thread.start()

while True:
    message = input()

    if message == DISCONNECT_MSG:
        client.send(message.encode())
        client.close()
        break
    else:
        send_msg(message)
    