import socket
import threading
import os
import shutil
from datetime import datetime
import GUI

IP = "127.0.0.1"
PORT = 12345
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
DIRECTORY = "directory"

commands = ["/join <server_ip_add> <port> - connect to the server application", 
            "/leave - disconnect to the server application", 
            "/register <handle> - register a unique handle or alias", 
            "/store <filename> - send file to server",
            "/dir - request directory file list from a server",
            "/get <filename> - fetch a file from a server",
            "/msg <username> <message> - privately message an online user",
            "/broadcast <message> - broadcast message to all online users",
            "/allusers - view all online users in the server",
            "/? - request command help to output all Input Syntax commands for references"]

client_registered = {}
uploaded_files = set(os.listdir(DIRECTORY))

def checkRegistered(conn):
    if client_registered[conn] is None:
        response = "You have to register first." 
        conn.sendall(response.encode(FORMAT))
    else:
        return 1
        
def broadcast(message):
    for client, username in client_registered.items():
        try:
            client.sendall(message)
        #just in case the user disconnects while sending
        except Exception as e:
            print(f"[ERROR] Error sending message to client: {e}")
                 

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

                #user asking for help
                if msg.startswith("/?"):
                    response = "\n--------- COMMAND LIST ----------\n"
                    for command in commands:
                        response += f"{command}\n"
                    conn.sendall(response.encode(FORMAT))

                #user registration
                elif msg.startswith("/register"):
                    if client_registered[conn] is not None:
                        response = "You have already registered." 
                        conn.sendall(response.encode(FORMAT))
                    else: 
                        try:
                            # Split message to extract username
                            _, username = msg.split(maxsplit=1)
                            if username in client_registered.values():
                                response = "Username already taken."
                                conn.sendall(response.encode(FORMAT))
                            else:
                                client_registered[conn] = username
                                #since nagkabaliktad, for verifiability lang ito (dont use for others)
                                response = f"[NEW USER] {username} has entered the server."

                                conn.sendall("pass".encode(FORMAT))
                                broadcast(response.encode(FORMAT))

                        except ValueError:
                            response = "Invalid syntax. Use: /register <handle>"
                            conn.sendall(response.encode(FORMAT))
                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)

                #user storing file
                elif msg.startswith("/store"):
                    if checkRegistered(conn) == 1:
                        try:
                            _, filename = msg.split(maxsplit=1)
                            
                            if not filename:
                                raise ValueError("Filename is empty.")
                            
                            source_path = os.path.join(os.getcwd(), filename)
                            destination_path = os.path.join(DIRECTORY, filename)
                            
                            if os.path.isfile(source_path):
                                shutil.copy(source_path, destination_path)
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                print(f"[{addr}] User {client_registered[conn]} <{timestamp}>: File {filename} moved to directory.")
                                response = f"{client_registered[conn]} <{timestamp}>: File '{filename}' uploaded successfully"
                                broadcast(response.encode(FORMAT))
                                uploaded_files.add(filename)

                            else:
                                response = f"File {filename} not found."
                                conn.sendall(response.encode(FORMAT))

                        except ValueError:
                            error_message = f"Invalid syntax. Use: /store <filename>"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)

                #user asks for directory
                elif msg == ("/dir"):
                    if checkRegistered(conn) == 1:
                        if len(uploaded_files) == 0:
                            response = "No files found in the directory."
                            conn.sendall(response.encode(FORMAT))

                        else:
                            try:
                                i = 0
                                response = "\n--------- CURRENT FILES IN DIRECTORY ----------\n"
                                for filename in uploaded_files:
                                    i += 1
                                    try:
                                        print(filename)
                                        response += f"File {i}: {filename}\n"
                                    except Exception as e:
                                        print(f"[ERROR] Failed to send filename {filename}: {e}")
                                        break
                            except Exception as e:
                                error_message = f"Unexpected error: {e}"
                                print(error_message)
                            conn.sendall(response.encode(FORMAT))

                #user getting file
                elif msg.startswith("/get"):
                    if checkRegistered(conn) == 1:
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

                        except ValueError:
                            error_message = f"Invalid syntax. Use: /get <filename>"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)

                #user messaging another user
                elif msg.startswith("/msg"):
                    if checkRegistered(conn) == 1:
                        try:
                            _, recipient, message = msg.split(maxsplit = 2)
                            recipient_conn = None
                            
                            # Find the connection object of the recipient
                            for c, user in client_registered.items():
                                if user == recipient:
                                    recipient_conn = c #find the recipient socket
                                    break
                                else:
                                    response = "Recipient not found."
                            
                            if recipient_conn != conn:
                                response = f"{client_registered[conn]}: {message}"
                                recipient_conn.sendall(response.encode(FORMAT))
                                response = f"Message to {recipient} sent successfully."

                            elif recipient == conn:
                                response = f"Message cannot be sent to yourself"

                        
                        except ValueError:
                            error_message = f"Invalid syntax. Use: /msg <username> <message>"
                            print(error_message)

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            del client_registered[recipient_conn]
                            response = "Recipient not found."
                            print(error_message)
                        conn.sendall(response.encode(FORMAT))
                      

                #user sending message to all clients
                elif msg.startswith("/broadcast"):
                    if checkRegistered(conn) == 1:
                        try:
                            _, message = msg.split(maxsplit=1)
                            response = f"[BROADCAST] {client_registered[conn]}: {message}"
                            broadcast(response.encode(FORMAT))
                            
                        except ValueError:
                            error_message = f"Invalid syntax. Use: /broadcast <message>"
                            print(error_message)
                            conn.sendall(error_message.encode(FORMAT))

                        except Exception as e:
                            error_message = f"Unexpected error: {e}"
                            print(error_message)

                # user trying to join again
                elif msg.startswith("/join"):
                    response = "You have already joined a server. Please use other commands."
                    conn.sendall(response.encode(FORMAT))

                elif msg.startswith("/allusers"):
                    response = "\n--------- CURRENT USERS IN SERVER ----------\n"
                    i = 0
                    for socket, users in client_registered.items():
                        i += 1
                        response += (f"User {i}: {users}\n")
                    conn.sendall(response.encode(FORMAT))

                #invalid command
                else:
                    response = "Command not found"
                    conn.sendall(response.encode(FORMAT))

            except (ConnectionAbortedError, ConnectionResetError):
                print(f"[DISCONNECTED] Connection with {addr} was aborted or reset.")
                break

            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                break

    finally:
        response = f"[BROADCAST] {client_registered[conn]} has left the server."
        broadcast(response.encode(FORMAT))
        conn.close()


def main():
        print(f"[STARTING] Server is starting...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # binds them to the ip and port 
        server.bind(ADDR)
        server.listen()
        server.settimeout(0.5)
        print(f"[LISTENING] Server is listening on {IP}:{PORT}")
        connected = True
        try:
            while connected:
                try:
                    # accept clients
                    conn, addr = server.accept()
                    thread = threading.Thread(target=handle_client, args = (conn, addr))
                    thread.start()
                    print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
                except socket.timeout:
                    pass
                except KeyboardInterrupt:
                    try:
                        if connected:
                            connected=False
                            print("[CLOSING] Server is closing...")
                            break
                    except:
                        pass
        finally:
            server.close()
            print("Server closed.") 

if __name__ == "__main__":
    main()
    


'''
Imported libraries:

threading - Allows multiple threads of execution on a Python program. Used so that a client can receive messages without waiting
for a command input.

shutil - Allows us to perform high-level operations on single and/or multiple files. Features include copying.
os - Allows us to interact with the operating system. Useful for managing directories.

References:

Python | Threading | Codecademy. (2022). Python | Threading | Codecademy. Codecademy. https://www.codecademy.com/resources/docs/python/threading

shutil — High-level file operations. (2024). Python Documentation. https://docs.python.org/3/library/shutil.html

W3Schools.com. (2024). W3schools.com. https://www.w3schools.com/python/module_os.asp

'''