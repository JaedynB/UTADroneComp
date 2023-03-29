import socket

SERVER = "irc.libera.chat"
PORT = 6667
CHANNEL = "#RTK..."
NICKNAME = "publisher"

def send_message(sock, message):
    sock.send(f"PRIVMSG {CHANNEL} :{message}\r\n".encode())
    
def parse_message(message):
    #Implement message parsing here
    pass
    
    
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER, PORT))
sock.send(f"NICK {NICKNAME}\r\n".encode())
sock.send(f"USER {USERNAME} 0 * :{REALNAME}\r\n".encode())
sock.send(f"JOIN {CHANNEL}\r\n".encode())

while True:
    data = sock.recv(1024).decode()
    if not data:
        break
    for line in data.split("\r\n"):
        parts = line.split()
        if len(parts) < 2:
            continue
        if parts[0] == "PING":
            sock.send(f"PONG {parts[1]}\r\n".encode())
        elif parts[1] == "PRIVMSG" and parts[2] == CHANNEL:
            message = " ".join(parts[3:])[1:]
            parse_message(message)
            
sock.close()

