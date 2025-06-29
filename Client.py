import socket
import threading

HOST = '127.0.0.1'  # Ganti dengan IP server jika di jaringan berbeda
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive_messages():
    while True:
        try:
            msg = client.recv(1024).decode('utf-8')
            if not msg:
                break
            print(msg, end='')  # end='' supaya tidak tambah newline otomatis
        except:
            print("\nDisconnected from server.")
            break

def send_messages():
    while True:
        try:
            # Input prompt simpel, tanpa 'You: '
            msg = input()
            if msg.lower() == 'exit':
                client.send(msg.encode('utf-8'))
                client.close()
                break
            client.send(msg.encode('utf-8'))
        except:
            break

# Start thread penerima pesan (daemon biar mati saat main thread mati)
threading.Thread(target=receive_messages, daemon=True).start()

# Loop input dan kirim pesan
send_messages()
