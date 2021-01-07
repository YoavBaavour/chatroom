import threading
import socket

PORT = 5055
SERVER_IP = "26.80.251.228"
ADDR = (SERVER_IP, PORT)
HEADER = 64
# create a socket with address family of internet IPs, and socket type)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the socket "client" to the server's address
client.connect(ADDR)



def write():
    while True:
        msg = f'{nickname}: {input()}'
        send_message(msg)


def send_message(message):
    # pad the message's length to fit the header's size
    padded_header = f'{len(message) :< {HEADER}}'
    # send a header of the message
    client.send(padded_header.encode("utf-8"))
    # send the message
    client.send(message.encode("utf-8"))


def receive_message():
    while True:
        try:
            # get message's header
            message_header = client.recv(HEADER).decode("utf-8")
            # get actual message
            message_length = int(message_header.strip())
            message = client.recv(message_length).decode("utf-8")

            # print the message received
            print(message)
            if message == "[CONNECTED] please set a nickname:":
                break

        except:
            print("error in receiving the message")
            client.close()
            break


receive_message()
nickname = input()
send_message(nickname)

# run receiving messages from the server on a different thread
receive_thread = threading.Thread(target=receive_message, args=())
receive_thread.start()

# run write messages to the server on the main thread
write()
