import os
import socket
import threading
import json
import smtplib
import queue
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ftplib import FTP

# Server configuration
HOST = '127.0.0.1'
PORT = 12345

# SMTP configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'ardalandehghan0@gmail.com'
SMTP_PASSWORD = 'xkrv smvt cxbz ltip'  

# FTP configuration
FTP_SERVER = "127.0.0.1"
FTP_USERNAME = "anonymous"
FTP_PASSWORD = ""
FTP_DIRECTORY = "ftp_files"

def receive_messages(client, response_queue):
    """Handle incoming messages from the server."""
    while True:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                break

            try:
                message = json.loads(data)
                if message.get("type") == "download_status":
                    response_queue.put(message)
                else:
                    print(f"\nReceived from server: {data}")
            except json.JSONDecodeError:
                print(f"\n[ERROR] Could not decode message: {data}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def send_email(to, subject, body):
    """Send an email using SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {to}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def upload_to_ftp(filename):
    ftp = FTP()
    ftp.connect(FTP_SERVER, 2121)
    ftp.login(FTP_USERNAME, FTP_PASSWORD)
    try:
        ftp.cwd(FTP_DIRECTORY)
    except:
        ftp.mkd(FTP_DIRECTORY)
        ftp.cwd(FTP_DIRECTORY)

    with open(filename, 'rb') as file:
        ftp.storbinary(f"STOR {filename}", file)
    ftp.quit()
    print(f"File {filename} uploaded successfully.")

def download_file(filename):
    try:
        ftp = FTP()
        ftp.connect(FTP_SERVER, 2121)
        ftp.login(FTP_USERNAME, FTP_PASSWORD)
        ftp.cwd(FTP_DIRECTORY)

        from io import BytesIO
        file_buffer = BytesIO()
        ftp.retrbinary(f"RETR {filename}", file_buffer.write)
        file_content = file_buffer.getvalue()
        ftp.quit()

        print(f"Downloaded {filename} successfully.")
        return file_content
    except Exception as e:
        print(f"Failed to download file from FTP server: {e}")
        return None

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    response_queue = queue.Queue()
    threading.Thread(target=receive_messages, args=(client, response_queue), daemon=True).start()

    try:
        while True:
            user_input = input("Enter a command (/chat, /email, /upload, /download): ")

            if user_input.startswith("/chat"):
                message = user_input[len("/chat "):]
                data = json.dumps({
                    "type": "chat",
                    "message": message
                }).encode('utf-8')
                client.sendall(data)

            elif user_input.startswith("/email"):
                parts = user_input[len("/email "):].split(" ", 2)
                if len(parts) == 3:
                    to, subject, body = parts
                    if send_email(to, subject, body):
                        data = json.dumps({
                            "type": "email_status",
                            "status": "sent"
                        }).encode('utf-8')
                        client.sendall(data)
                else:
                    print("Invalid email format. Use: /email <to> <subject> <body>")

            elif user_input.startswith("/upload"):
                filename = user_input[len("/upload "):]
                try:
                    if os.path.getsize(filename) == 0:
                        print("⚠️ Warning: File is empty before uploading!")
                    upload_to_ftp(filename)
                    data = json.dumps({
                        "type": "upload",
                        "filename": filename,
                        "status_upload": 200
                    }).encode('utf-8')
                    client.sendall(data)
                except FileNotFoundError:
                    print(f"File {filename} not found.")
                    data = json.dumps({
                        "type": "upload",
                        "filename": filename,
                        "status_upload": 500
                    }).encode('utf-8')
                    client.sendall(data)

            elif user_input.startswith("/download"):
                filename = user_input[len("/download "):]
                request = json.dumps({
                    "type": "download",
                    "filename": filename
                }).encode('utf-8')
                client.sendall(request)

                try:
                    message = response_queue.get(timeout=3)
                except queue.Empty:
                    print("❌ No response from server for download request.")
                    continue

                if message["type"] == "download_status" and message["status"].lower() == "ok":
                    print(f"Server is ready to download {filename}. Now proceeding to download the file from FTP.")
                    file_content = download_file(filename)

                    if file_content:
                        # Save it locally
                        download_path = f"downloaded_{filename}"
                        with open(download_path, "wb") as f:
                            f.write(file_content)

                        print(f"✅ File saved locally as {download_path}")

                        # Try to print content (if it's a text file)
                        try:
                            print("📄 File content:\n" + file_content.decode('utf-8'))
                        except UnicodeDecodeError:
                            print("📦 File saved successfully (binary or non-text content)")
                    else:
                        print("❌ Failed to download file content from FTP.")
                else:
                    print("❌ Failed to receive OK from server for downloading the file.")

            else:
                print("Invalid command.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    start_client()
