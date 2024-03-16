# app.py

from flask import Flask, request, session, redirect, url_for, render_template, jsonify
import threading
import socket
import json
from functools import wraps
import queue

app = Flask(__name__)
app.secret_key = "c00kiemik"

connected_connections = []
connected_addresses = []
server_log = []

# Fila para armazenar as respostas dos clientes
response_queue = queue.Queue()

def require_login(view):
    @wraps(view)
    def decorated_view(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return decorated_view

@app.route('/start_server', methods=['POST'])
@require_login
def start_server():
    host = request.form['host']
    port = int(request.form['port'])

    server_thread = threading.Thread(target=start_socket, args=(host, port))
    server_thread.daemon = True
    server_thread.start()

    return jsonify({'status': 'success', 'message': f'Server started successfully on {host}:{port}!'})

def start_socket(host, port):
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(5)
    add_log(f'[+] Socket bound successfully to {host} on port {port}')

    accept_connections(server_socket)

def accept_connections(server_socket):
    while True:
        client_socket, client_address = server_socket.accept()
        server_socket.setblocking(1)
        connected_connections.append(client_socket)
        connected_addresses.append(client_address)
        add_log(f'[+] Client connected to {client_address[0]}')

@app.route('/list_connections', methods=['GET'])
@require_login
def list_connections():
    connections = [{'id': i, 'address': f'{addr[0]}:{addr[1]}'} for i, addr in enumerate(connected_addresses)]
    return jsonify(connections)

def load_users():
    with open('../users.json') as f:
        return json.load(f)['users']

def process_login(username, password):
    users = load_users()
    for user in users:
        if username == user['username'] and user['password'] == password:
            return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if process_login(username, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return 'Login failed. Please check your credentials.'
    return render_template('login.html')
    
@app.route('/send_message', methods=['POST'])
@require_login
def send_message():
    try:
        target_id = int(request.form['targetId'])
        message = request.form['message']
        target_connection = connected_connections[target_id]
        target_connection.send(str.encode(message))
        return jsonify({'status': 'success', 'message': 'Message sent successfully'})
    except (IndexError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid target ID'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error sending message: {e}'})

@app.route('/send_message_and_wait', methods=['POST'])
@require_login
def send_message_and_wait():
    try:
        target_id = int(request.form['targetId'])
        message = request.form['message']
        target_connection = connected_connections[target_id]
        target_connection.send(str.encode(message))
        # Aguardar resposta do cliente
        response = target_connection.recv(1024).decode()
        return jsonify({'status': 'success', 'message': response})
    except (IndexError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid target ID'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error sending message and waiting for response: {e}'})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@require_login
def home():
    return render_template('home.html')

@app.route('/get_logs', methods=['GET'])
@require_login
def get_logs():
    return jsonify(server_log)

def add_log(message):
    server_log.append(message)
    if len(server_log) > 50:
        del server_log[0]

if __name__ == "__main__":
    app.run(debug=True)
