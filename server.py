import socket
import threading
import os
import shutil
from datetime import datetime

IP = "127.0.0.1"
PORT = 12345
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
DISCONNECT_MSG = "/leave"
DIRECTORY = "directory"

client_registered = {}
registered = {}
uploaded_files = set(os.listdir(DIRECTORY))

        
def broadcast(message, curr_client):
    clients_to_remove = []
    for client, username in client_registered.items():
        if client != curr_client:
            try:
                client.sendall(message)

            #just in case the user disconnects while sending
            except Exception as e:
                print(f"Error sending message to client: {e}") 
                clients_to_remove.append(username)
    for username in clients_to_remove:
        del client_registered[username] 

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
                    print(f"[{conn}] Disconnected.")
                    connected = False

                #user asking for help
                elif msg.startswith("/?"):
                    conn.sendall(("help").encode(FORMAT))

                #user registration
                elif msg.startswith("/register"):
                    if client_registered[conn] is not None:
                        response = "You have already registered."    

                    else: 
                        try:
                            # Split message to extract username
                            _, username = msg.split(maxsplit=1)
                            if username in registered:
                                response = "Username already taken."
                            else:
                                client_registered[conn] = username

                                #since nagkabaliktad, for verifiability lang ito (dont use for others)
                                registered[username] = conn
                                response = "Registration successful."

                        except ValueError:
                            response = "Invalid registration syntax. Use: /register <handle>"
                            
                    conn.sendall(response.encode(FORMAT))

                #user storing file
                elif msg.startswith("/store"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.sendall(response.encode(FORMAT))

                    else:
                        try:
                            _, filename = msg.split(maxsplit=1)
                            
                            if not filename:
                                raise ValueError("Filename is empty.")
                            
                            source_path = os.path.join(os.getcwd(), filename)
                            destination_path = os.path.join(DIRECTORY, filename)
                            
                            if os.path.isfile(source_path):
                                shutil.copy(source_path, destination_path)
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                print(f"[{addr}] User {client_registered[conn]} File {filename} moved to directory.")
                                response = f"{client_registered[conn]} <{timestamp}>: File '{filename}' uploaded successfully"
                                broadcast(response.encode(FORMAT),client_registered)
                                uploaded_files.add(filename)

                            else:
                                response = f"File {filename} not found."
                                conn.sendall(response.encode(FORMAT))

                        except ValueError as ve:
                            error_message = f"Error: {ve}"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                #user asks for directory
                elif msg == ("/dir"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.sendall(response.encode(FORMAT))

                    else:
                        if len(uploaded_files) == 0:
                            response = "No files found in the directory."
                            conn.sendall(response.encode(FORMAT))

                        else:
                            response = "Current files inside the directory:\n" 
                            for filename in uploaded_files:
                                try:
                                    print(filename)
                                    response += filename + "\n"
                                except Exception as e:
                                    print(f"[ERROR] Failed to send filename {filename}: {e}")
                                    break
                            conn.sendall(response.encode(FORMAT))

                #user getting file
                elif msg.startswith("/get"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.sendall(response.encode(FORMAT))
                    
                    else:
                        try:
                            _, filename = msg.split(maxsplit=1)
                            source_path = os.path.join(DIRECTORY, filename)
                            destination_path = os.path.join(os.getcwd(), filename)
                            found = False

                            if os.path.isfile(source_path):
                                shutil.copy(source_path, destination_path)
                                print(f"[{addr}] User {client_registered[conn]} File {filename} downloaded from directory.")
                                response = f"File {filename} has been downloaded from the {DIRECTORY}."
                                found = True

                            if found == False:
                                response = f"{filename} not found."
                            
                            conn.sendall(response.encode(FORMAT))

                        except ValueError as ve:
                            error_message = f"Error: {ve}"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                #user messaging another user
                elif msg.startswith("/msg"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.sendall(response.encode(FORMAT))

                    else:
                        _, recipient, message = msg.split(" ", 2)
                        recipient_conn = None
                        
                        # Find the connection object of the recipient
                        for c, user in client_registered.items():
                            if user == recipient:
                                recipient_conn = c #find the recipient username
                                break
                        
                        if recipient_conn != conn:
                            response = f"{client_registered[conn]}: {message}"
                            recipient_conn.sendall(response.encode(FORMAT))
                            response = f"Message to {recipient} sent successfully."
                            conn.sendall(response.encode(FORMAT))
                        elif recipient_conn == conn:
                            response = f"Message cannot be sent to yourself"
                            conn.sendall(response.encode(FORMAT))
                        else:
                            response = "Recipient not found."
                            conn.sendall(response.encode(FORMAT))

                #user sending message to all clients
                elif msg.startswith("/broadcast"):
                    if client_registered[conn] is None:
                        response = "You have to register first." 
                        conn.sendall(response.encode(FORMAT))
                    
                    else:
                        _, message = msg.split(maxsplit=1)
                        response = f"[BROADCAST] {client_registered[conn]}: {message}"
                        broadcast(response.encode(FORMAT),client_registered)

                # user trying to join again
                elif msg.startswith("/join"):
                    response = "You have already joined a server. Please use other commands."
                    conn.sendall(response.encode(FORMAT))

                #invalid command
                else:
                    response = "Command not found"
                    conn.sendall(response.encode(FORMAT))

            except (ConnectionAbortedError, ConnectionResetError):
                print(f"[ERROR] Connection with {addr} was aborted or reset.")
                break

            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                break

    finally:
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
