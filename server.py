import threading
import socket


PORT = 5055
SERVER_IP = '26.80.251.228'
# SERVER_IP = '192.168.1.2'
ADDR = (SERVER_IP, PORT)
HEADER = 64

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()

sockets_dict = {server: {"address": ADDR, "nickname": "server"}}


def handle_disconnection(client_socket):
    nickname = sockets_dict[client_socket]['nickname']  # save nickname for DC message
    broadcast(f'[{nickname}] HAS DISCONNECTED!', client_socket)
    print(f'[{nickname}] HAterS DISCONNECTED!')
    del sockets_dict[client_socket]  # delete socket from list of sockets
    client_socket.close()  # close socket connection to the server

def handle_connection(client_socket):
    while True:
        try:
            message_header = client_socket.recv(HEADER).decode("utf-8")
            msg_len = int(message_header)
            message = client_socket.recv(msg_len).decode("utf-8")
            broadcast(message, client_socket)

        except:     # client disconnected
            handle_disconnection(client_socket)
            break                                 # break out of the while loop and end current thread


def broadcast(message, client_socket):
    # create a list of all sockets in the connection and send the message to all of them but the server
    sockets_list = sockets_dict.keys()

    for client in sockets_list:
        if sockets_dict[client]['nickname'] != "server" and \
           sockets_dict[client]['nickname'] != sockets_dict[client_socket]['nickname']:
            send_message(client, message)



def send_message(client_socket, message):
    # pad the message's length to fit the header's size
    padded_header = f'{len(message) :< {HEADER}}'
    # send a header of the message
    client_socket.send(padded_header.encode("utf-8"))
    # send the message
    client_socket.send(message.encode("utf-8"))


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER).decode("utf-8")
        if len(message_header) == 0:
            return 0
        message_length = int(message_header.strip())

        message = client_socket.recv(message_length).decode("utf-8")
        return {"header": message_header, "data": message}

    except:  # most likely will trigger when a client disconnects
        return 0


def connections():
    print("[LISTENING] for new connections...")
    while True:
        # accept an incoming connection
        client_socket, client_addr = server.accept()

        # send a message to a specific client (ask for a nickname)
        send_message(client_socket, "[CONNECTED] please set a nickname:")

        # receive nickname chosen by client
        message = receive_message(client_socket)
        if not message:          # message is False  or empty dict
            continue
        client_nickname = message["data"]

        # add client's nickname and its address to clients dict
        sockets_dict[client_socket] = {"address": client_addr, "nickname": client_nickname}

        # send message to all clients connected to server
        welcome_message = f'[{client_nickname}] JOINED THE CHAT!'
        broadcast(welcome_message, client_socket)
        print(welcome_message)

        # create a thread to handle each connection "simultaneously"
        thread = threading.Thread(target=handle_connection, args=(client_socket,))
        thread.start()


connections()
