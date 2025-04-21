import os
import socket
import threading
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ftplib import FTP

# Server configuration
HOST = '127.0.0.1'
PORT = 12345

# FTP configuration (local)
FTP_SERVER = "127.0.0.1"
FTP_USERNAME = "anonymous"
FTP_PASSWORD = ""
FTP_DIRECTORY = "ftp_files"

# Classroom state
clients = {}
client_id_counter = 1

# Ensure the FTP directory exists
if not os.path.exists(FTP_DIRECTORY):
    os.makedirs(FTP_DIRECTORY)

def broadcast(message):
    for client in clients:
        try:
            client.sendall(message.encode('utf-8'))
        except:
            pass

def list_files():
    ftp = FTP()
    ftp.connect(FTP_SERVER, 2121)
    ftp.login(FTP_USERNAME, FTP_PASSWORD)
    ftp.cwd(FTP_DIRECTORY)
    files = ftp.nlst()
    ftp.quit()
    return files

def download_file(filename):
    try:
        ftp = FTP()
        ftp.connect(FTP_SERVER, 2121)
        ftp.login(FTP_USERNAME, FTP_PASSWORD)
        ftp.cwd(FTP_DIRECTORY)
        from io import BytesIO
        buffer = BytesIO()
        ftp.retrbinary(f"RETR {filename}", buffer.write)
        file_content = buffer.getvalue()
        ftp.quit()
        print(f"Downloaded {filename} successfully.")
        return file_content
    except Exception as e:
        print(f"Failed to download file from FTP server: {e}")
        return None

def server_command_interface():
    while True:
        command = input("\nEnter command (/chat, /listdir ,/download): ")

        if command.startswith("/chat"):
            msg = command[len("/chat "):]
            broadcast(json.dumps({"type": "chat", "from": "Server", "message": msg}))
            print(f"Sent message: {msg}")

        elif command.startswith("/listdir"):
            files = list_files()
            files_str = "\n".join(files) if isinstance(files, list) else files
            print(f"Files in FTP:\n{files_str}")

        elif command.startswith("/download"):
            filename = command[len("/download "):]
            content = download_file(filename)
            if content:
                print(content.decode('utf-8'))

def handle_client(client, address):
    global client_id_counter
    client_id = client_id_counter
    client_id_counter += 1
    clients[client] = {"id": client_id, "name": f"Student {client_id}"}

    print(f"New connection from {address} with ID {client_id}")
    welcome_message = f"Welcome to the virtual classroom! Your ID is {client_id}."
    print(f"Sending to client {client_id}: {welcome_message}")
    client.sendall(json.dumps({"type": "welcome", "message": welcome_message}).encode('utf-8'))

    broad_msg = f"{clients[client]['name']} has joined the classroom."
    broadcast(json.dumps({"type": "status", "message": broad_msg}))

    try:
        while True:
            data = client.recv(4096).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            print(f"\nReceived from client {client_id}: {data}")

            if message["type"] == "chat":
                data = json.dumps({
                    "type": "chat",
                    "from": clients[client]["name"],
                    "message": message["message"]
                })
                broadcast(data)

            elif message["type"] == "email_status":
                if message.get("status") == "sent":
                    data = json.dumps({
                        "type": "email_status",
                        "status": "success",
                        "message": "Email Received"
                    }).encode('utf-8')
                    client.sendall(data)

            elif message["type"] == "upload":
                filename = message["filename"]
                status_upload = message["status_upload"]
                if status_upload == 200:
                    files = list_files()
                    if filename in files:
                        data = json.dumps({
                            "type": "upload_status",
                            "status": "success",
                            "message": f"File {filename} has been uploaded to FTP server Successfully."
                        }).encode('utf-8')
                    else:
                        data = json.dumps({
                            "type": "upload_status",
                            "status": "error",
                            "message": f"File {filename} not found on FTP server."
                        }).encode('utf-8')
                    client.sendall(data)

            elif message["type"] == "download":
                filename = message["filename"]
                files = list_files()
                if filename in files:
                    data = json.dumps({
                        "type": "download_status",
                        "filename": filename,
                        "status": "ok",
                        "message": f"Ready to download file {filename}."
                    }).encode('utf-8')
                else:
                    data = json.dumps({
                        "type": "download_status",
                        "filename": filename,
                        "status": "error",
                        "message": f"File {filename} not found on FTP server."
                    }).encode('utf-8')
                client.sendall(data)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        left_msg = f"{clients[client]['name']} has left the classroom."
        del clients[client]
        client.close()
        broadcast(json.dumps({"type": "status", "message": left_msg}))

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server started on {HOST}:{PORT}")
    threading.Thread(target=server_command_interface, daemon=True).start()
    while True:
        client, address = server.accept()
        threading.Thread(target=handle_client, args=(client, address), daemon=True).start()

if __name__ == "__main__":
    start_server()
