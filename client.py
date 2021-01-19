import tkinter as tk
import threading
import socket
from tkinter import simpledialog

new_messages_flag = True         # flag to indicate if "new messages" message should be printed
need_to_set_nickname_flag = True         # flag to set a nickname one time with the server
nickname = None                   # global variable that hold this client's nickname

PORT = 5055
SERVER_IP = socket.gethostbyname(socket.gethostname())
# SERVER_IP = "192.168.1.18"

ADDR = (SERVER_IP, PORT)
HEADER = 64
# create a socket with address family of internet IPs, and socket type)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the socket "client" to the server's address
client.connect(ADDR)


def print_message(msg, my_message_flag=False):
    # link global var into function scope
    global new_messages_flag

    # handle client's message to show up on their screen (without the nickname)
    if my_message_flag:
        msg = msg[msg.find(':')+1::]
        msg_label = tk.Label(msg_frame, text=msg, bg="gray30", disabledforeground="burlywood2",
                             font=("Courier", 16), state='disabled', wraplength=1150)
        msg_label.pack(anchor='ne', padx=15)
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1)
        return

    # create the message's label for broadcast by the server to all other clients
    msg_label = tk.Label(msg_frame, text=msg, bg="gray30", disabledforeground="burlywood2",
                         font=("Courier", 16), state='disabled', wraplength=1150)

    # if scrollbar is at bottom of chat (new messages will be visible)
    if canvas_sb.get()[1] > 0.9:
        new_messages_flag = True
        msg_label.pack(anchor='nw', padx=10)
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1)

    else:
        # send a "new messages" message if scrollbar isn't at bottom of chat, AND said message wasn't sent already
        if new_messages_flag:
            # create "new messages" label
            new_messages = tk.Label(msg_frame, text="∙∙∙---=== new messages ===---∙∙∙", bg="gray30", disabledforeground="burlywood2",
                                    font=("Courier", 16), state='disabled', wraplength=1150)
            # send "new messages" message
            new_messages.pack(anchor='center', padx=10)
            new_messages_flag = False

        msg_label.pack(anchor='nw', padx=10)


def send_message(event=None, message=None):
    global need_to_set_nickname_flag

    # grab message from chat msg_bar
    if not need_to_set_nickname_flag:
        # grab text from msg_bar widget
        message = msg_bar.get(1.0, tk.END)
        # check if empty message
        if message == '\n':
            return 'break'
        message = message.strip('\n')
        message = f'{nickname}: {message}'
        # delete text in msg_bar
        msg_bar.delete(1.0, tk.END)

    # pad the message's length to fit the header's size
    try:
        padded_header = f'{len(message) :< {HEADER}}'
        # send a header of the message
        client.send(padded_header.encode("utf-8"))
        # send the message
        client.send(message.encode("utf-8"))
        if not need_to_set_nickname_flag:
            print_message(message, True)
        need_to_set_nickname_flag = False
        return "break"                              # returning "break" prevents a newline from appearing in the text widget
                                                    # after pressing it (to send messages)
    except Exception as e:
        return "break"


def handle_received_message():
    while True:
        try:
            # get message's header
            message_header = client.recv(HEADER).decode("utf-8")
            # get actual message
            message_length = int(message_header.strip())
            message = client.recv(message_length).decode("utf-8")

            if message == "[CONNECTED] please set a nickname:"\
                    or message == '/changenickname':
                print_message(message)
                set_nickname()
                # send chosen nickname to server
                send_message(message=nickname)
                print_message(f'[LOGGED IN] WELCOME {nickname}!')
                continue
            print_message(message)

        except Exception as e:
            print(f"{e}")
            client.close()
            break


def set_nickname():
    global nickname
    # popup window prompts user to enter nickname, saved into 'nickname' variable as string
    temp = tk.Tk()
    temp.withdraw()         # make window hidden
    while nickname == '' or nickname is None:
        nickname = simpledialog.askstring(title='Nickname', prompt='Please enter your nickname:', parent=temp)
    temp.destroy()
    # enable option to send messages
    msg_bar.configure(state='normal')


def close_connection():
    root.destroy()
    client.close()


# setup main window
root = tk.Tk()
root.title("Chatroom")
root.config(bg="red")
root.geometry("1200x800")
# root.resizable(False, False)

# modify pressing the 'X' button to close the gui to also close the connection to the server
root.protocol('WM_DELETE_WINDOW', func=close_connection)
# create top frame - for showing messages
top_frame = tk.Frame(root, borderwidth=2, width=1200, height=610, padx=10, pady=10, bg="gray30", relief='sunken')
# disable frame resizing
top_frame.place(relwidth=1, relheight=0.7625)

# create a canvas for the top_frame to display messages on it
chat_canvas = tk.Canvas(top_frame, bg="gray30", height=580, width=1160, highlightbackground="gray25")

# create frame on the canvas in which messages will show up required for scrolling option to work https://bit.ly/35HDBAn
msg_frame = tk.Frame(chat_canvas, bg="blue", height=550, width=1160)

# create a scrollbar for the canvas
canvas_sb = tk.Scrollbar(top_frame, orient='vertical', command=chat_canvas.yview)
chat_canvas.configure(yscrollcommand=canvas_sb.set)

# place canvas and scrollbar on the top_frame
chat_canvas.place(relwidth=0.98, relheight=1, width=1160)
canvas_sb.place(relx=0.985, relheight=1)


# create a window on the canvas to display the widgets on it
chat_canvas.create_window((0, 0), window=msg_frame, anchor='nw', tags="msg_frame", width=chat_canvas.winfo_width())

# TODO: fix resizing of top_frame, chat_canvas and msg_frame to fit all together
def on_msg_frame_configure(event):
    # set canvas size as new 'stretched' frame size
    chat_canvas.configure(height=msg_frame.winfo_height(), width=top_frame.winfo_width())
    chat_canvas.configure(scrollregion=chat_canvas.bbox('msg_frame'))
    msg_frame.place(width=top_frame.winfo_width() - canvas_sb.winfo_width() - 20)


def on_top_frame_configure(event):
    # msg_frame.configure(width=top_frame.winfo_width(), height=top_frame.winfo_height())
    on_msg_frame_configure(event)
    print(f'top_frame width={top_frame.winfo_width()}')
    print(f'chat_canvas width={chat_canvas.winfo_width()}')
    print(f'msg_frame width={msg_frame.winfo_width()}')


def set_mousewheel(widget, command):
    widget.bind("<Enter>", lambda e: widget.bind_all('<MouseWheel>', command))
    widget.bind("<Leave>", lambda e: widget.unbind_all('<MouseWheel>'))

# TODO: fix msg_frame stretching when resizing root window
#might beb a solution:
# https://stackoverflow.com/questions/5860491/tkinter-determine-widget-position-relative-to-root-window

# when a change happens on the msg_frame, update the scroll-region of the canvas
# msg_frame.bind(sequence='<Configure>', func=on_msg_frame_configure)
top_frame.bind(sequence='<Configure>', func=on_top_frame_configure)
# bind mousewheel to navigate msg_frame no matter what window is focused
set_mousewheel(chat_canvas, lambda ev: chat_canvas.yview_scroll(int(-1 * (ev.delta // 60)), 'units'))

# ---------------------------------------------------------------------------------------------------------------------#
# ---------------------------------------------------bottom frame----------------------------------------------------- #
# ---------------------------------------------------------------------------------------------------------------------#

# create frame for messages to be written and sent in
bottom_frame = tk.Frame(root, borderwidth=2, height=150, width=1200, padx=5,
                        pady=11, bg="gray30", relief='sunken')

# set frames sizes to fit one above the other in the main window's grid
bottom_frame.place(rely=0.7625, relheight=0.2375, relwidth=1)

# create text widget to insert messages in
msg_bar = tk.Text(bottom_frame, width=80, height=7, bg="gray30", fg="burlywood2", font=("Courier", 16), state='disabled')

# create button widget to send messages with
send_button = tk.Button(bottom_frame, anchor=tk.CENTER, padx=25, pady=40, bg="gray30", fg='burlywood2', relief='groove',
                        font=("Courier", 16, "bold"), text='Submit', command=send_message)

# create button widget to clear the text in the msg_bar
clear_button = tk.Button(bottom_frame, anchor=tk.CENTER, padx=25, bg="gray30", fg='burlywood2', relief='groove',
                         font=("Courier", 16, "bold"), text='Clear', command=lambda: msg_bar.delete(1.0, tk.END))

# bind pressing enter to send the message
# msg_bar.bind(sequence='<Return>', func=send_message)
msg_bar.bind(sequence='<Return>', func=lambda ev: send_message(event=ev, message=None))

msg_bar.bind(sequence='<Shift-Return>', func=lambda event: '\n')

# set the grid of the bottom_frame (text and button widgets)
msg_bar.place(relwidth=0.85, relheight=1)
send_button.place(relx=0.85, relheight=0.7, relwidth=0.15)
clear_button.place(relx=0.85, rely=0.7, relheight=0.3, relwidth=0.15)

# initialize communication with server (approval connection messages and set nickname)
# run receiving messages from the server on a different thread
receive_thread = threading.Thread(target=handle_received_message, args=())
receive_thread.start()

root.mainloop()
