import socket
import threading
import os
import shutil

IP = "127.0.0.1"
PORT = 12345
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
DISCONNECT_MSG = "/leave"
DIRECTORY = "directory"

registered_users = {}
client_registered = {}
uploaded_files = set(os.listdir(DIRECTORY))

commands = ["/join <server_ip_add> <port> - connect to the server application", 
            "/leave - disconnect to the server application", 
            "/register <handle> = register a unique handle or alias", 
            "/store <filename> - send file to server",
            "/dir - request directory file list from a server",
            "/get <filename> - fetch a file from a server",
            "/? - request command help to output all Input Syntax commands for references"]

#in progress
def process_syntax(user_input):
        
    #if client enters "/leave"
        if user_input == DISCONNECT_MSG:
            print("[CLIENT] Leaving...")
        
        elif user_input == "/?":
            i = 0
        else:
            print("Invalid syntax. For more help, see '/?' for your references")

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    client_registered[conn] = None

    try:
        while connected:
            try:
                # Receive message from client
                msg = conn.recv(SIZE).decode(FORMAT)
                if not msg:
                    continue

                #disconnect
                if msg == DISCONNECT_MSG:
                    print(f"[{addr}] Disconnected.")
                    connected = False

                #user asking for valid syntax
                elif msg.startswith("/?"):
                    conn.send(("help").encode(FORMAT))

                #user registration
                elif msg.startswith("/register"):
                    if client_registered[conn] is not None:
                        response = "You have already registered."    

                    else: 
                        try:
                            # Split message to extract username
                            _, username = msg.split(maxsplit=1)
                            if username in registered_users:
                                response = "Username already taken."

                            else:
                                registered_users[conn] = username
                                client_registered[conn] = username
                                response = "Registration successful."

                        except ValueError:
                            response = "Invalid registration syntax. Use: /register <handle>"
                            
                    conn.send(response.encode(FORMAT))

                #user storing file
                elif msg.startswith("/store"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.send(response.encode(FORMAT))

                    else:
                        try:
                            _, filename = msg.split(maxsplit=1)
                            
                            if not filename:
                                raise ValueError("Filename is empty.")
                            
                            source_path = os.path.join(os.getcwd(), filename)
                            destination_path = os.path.join(DIRECTORY, filename)
                            
                            if os.path.isfile(source_path):
                                shutil.copy(source_path, destination_path)
                                print(f"[{addr}] User {registered_users[conn]} File {filename} moved to directory.")
                                response = f"File {filename} copied to {DIRECTORY} successfully."
                                uploaded_files.add(filename)

                            else:
                                response = f"File {filename} not found."

                            conn.send(response.encode(FORMAT))

                        except ValueError as ve:
                            error_message = f"Error: {ve}"
                            print(error_message)
                            conn.send(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)
                            conn.send(error_message.encode(FORMAT))

                #user asks for directory
                elif msg == ("/dir"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.send(response.encode(FORMAT))

                    else:
                        if len(uploaded_files) == 0:
                            response = "No files found in the directory."
                            conn.send(response.encode(FORMAT))

                        else:
                            response = "Current files inside the directory:\n" 
                            for filename in uploaded_files:
                                try:
                                    print(filename)
                                    response += filename + "\n"
                                except Exception as e:
                                    print(f"[ERROR] Failed to send filename {filename}: {e}")
                                    break
                            conn.send(response.encode(FORMAT))

                #user getting file
                elif msg.startswith("/get"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.send(response.encode(FORMAT))
                    
                    else:
                        try:
                            _, filename = msg.split(maxsplit=1)
                            source_path = os.path.join(DIRECTORY, filename)
                            destination_path = os.path.join(os.getcwd(), filename)
                            found = False

                            if os.path.isfile(source_path):
                                shutil.copy(source_path, destination_path)
                                print(f"[{addr}] User {registered_users[conn]} File {filename} downloaded from directory.")
                                response = f"File {filename} has been downloaded from the {DIRECTORY}."
                                found = True

                            if found == False:
                                response = f"{filename} not found."
                            
                            conn.send(response.encode(FORMAT))

                        except ValueError as ve:
                            error_message = f"Error: {ve}"
                            print(error_message)
                            conn.send(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)
                            conn.send(error_message.encode(FORMAT))

                #user messaging another user
                elif msg.startswith("/msg"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.send(response.encode(FORMAT))

                    else:
                        _, recipient, message = msg.split(" ", 2)
                        recipient_conn = None
                        
                        # Find the connection object of the recipient
                        for c, user in client_registered.items():
                            if user == recipient:
                                recipient_conn = c
                                break
                        
                        if recipient_conn:
                            response = f"{client_registered[conn]}: {message}"
                            recipient_conn.send(response.encode(FORMAT))
                            response = f"Message to {recipient} sent successfully."
                            conn.send(response.encode(FORMAT))
                        else:
                            response = "Recipient not found."
                            conn.send(response.encode(FORMAT))

                #user sending message to all clients
                elif msg.startswith("/broadcast"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.send(response.encode(FORMAT))
                    continue

                # user trying to join again
                elif msg.startswith("/join"):
                    response = "You have already joined a server. Please use other commands."
                    conn.send(response.encode(FORMAT))

                #invalid command
                else:
                    response = "Command not found"
                    conn.send(response.encode(FORMAT))

            except (ConnectionAbortedError, ConnectionResetError):
                print(f"[ERROR] Connection with {addr} was aborted or reset.")
                break

            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                break

    finally:
        if client_registered[conn] is not None:
            registered_users.discard(client_registered[conn])

        del client_registered[conn] 
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")

def main():
    print(f"[STARTING] Server is starting...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # binds them to the ip and port 
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening on {IP}:{PORT}")

    while True:
        # accept clients
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args = (conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    main()
