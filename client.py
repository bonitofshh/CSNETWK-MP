import socket
import threading

IP = "127.0.0.1"
PORT = 12345
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
DISCONNECT_MSG = "/leave"   

INPUTSYNTAX = ["/join", "/leave", "/register", "/store", "/dir", "/get", "/?"]

commands = ["/join <server_ip_add> <port> - connect to the server application", 
            "/leave - disconnect to the server application", 
            "/register <handle> = register a unique handle or alias", 
            "/store <filename> - send file to server",
            "/dir - request directory file list from a server",
            "/get <filename> - fetch a file from a server",
            "/msg <username> <message> - privately message an online user",
            "/broadcast <message> - broadcast message to all online users",
            "/? - request command help to output all Input Syntax commands for references"]

# process the user_input before joining
def process_syntax(user_input):
    split_input = user_input.split()
    
    if split_input[0] == "/join" and len(split_input) == 3 :
            if split_input [1] == "127.0.0.1" and split_input[2] == "12345":
                return 1
            elif split_input [1] != "127.0.0.1" or split_input[2] != "12345":
                print("[ERROR] Connection to the Server has failed! Please check IP Address and Port Number.")
    elif split_input[0] == "/join" and len(split_input) != 3:
        print("[ERROR] Command parameters do not match. Do you mean /join <IP Address> <Port>?") 
    elif split_input[0] == "/?":
        for command in commands:
            print(f"{command}")
    elif split_input[0] in INPUTSYNTAX:
        print("[ERROR] Please join a server first.")
    else:
        print("[ERROR] Command not found.")


def receive_messages(client):
    while True:
        try:
            msg = client.recv(SIZE).decode(FORMAT)
            if msg == "help":
                for command in commands:
                    print(f"{command}")

            else:
                print(f"[SERVER] {msg}")
        except Exception as e:
            print(f"[ERROR] Failed to receive message: {e}")
            break

def main():

    # loops until user enters /join syntax
    while True: 
        msg = input("> ")
        syntax = process_syntax(msg)
        if syntax == 1:
            break

    # will access once broken from while loop
    if process_syntax(msg) == 1:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print(f"[CONNECTED] Client connected to server at {IP}:{PORT}")

            receive_thread = threading.Thread(target=receive_messages, args=(client,))
            receive_thread.start()
            
            connected = True
            while connected:
                msg = input("> ")
                #sends the message to client
                client.send(msg.encode(FORMAT))
                if msg == DISCONNECT_MSG:
                    connected = False

        except socket.error as e:
            print(f"[ERROR] Socket error: {e}")

        finally:
            client.close()
            print("[DISCONNECTED] Client disconnected.")    

if __name__ == "__main__":
    main()