# Virtual Classroom System - CN Homework

A simple local client-server system for a **virtual classroom** built using Python `socket`, `FTP`, and `SMTP`. This project was developed as part of a **Computer Networks** course assignment.

## 📌 Features

-  TCP-based multi-client chatroom (students & teacher)
-  Email sending feature from student to teacher (SMTP)
-  File upload to FTP server (assignments, notes, etc.)
-  File download from FTP server with content preview
-  Broadcast messages from server to all connected clients

##  Technologies Used

- Python 3.x
- `socket`, `threading`, `json`, `smtplib`, `ftplib`
- Local FTP server using [`pyftpdlib`](https://github.com/giampaolo/pyftpdlib)

##  Project Structure

## How to Run (Locally)


```bash
pip install pyftpdlib
python3 server.py
python3 client.py
/chat <message> – send a message to the classroom

/email <to> <subject> <body> – send email to teacher

/upload <filename> – upload file to FTP server

/download <filename> – download file and view contents
