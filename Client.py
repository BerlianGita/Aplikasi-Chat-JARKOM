import socket
import threading
from tester import get_server_ip  # Fungsi eksternal untuk dapatkan IP server (jika ada)

PORT = 12345
HOST = get_server_ip(port=PORT) or '127.0.0.1'  # Default ke localhost kalau gak dapat IP server

# Membuat socket TCP client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Coba konek ke server
    client.connect((HOST, PORT))
except Exception as e:
    print(f"Gagal connect ke server {HOST}:{PORT} - {e}")
    exit(1)

username = ""  # Variabel simpan username user
in_chatroom = False  # Flag untuk menandakan user sudah masuk room chat atau belum

def receive_messages():
    """Thread untuk menerima dan menampilkan pesan dari server"""
    while True:
        try:
            msg = client.recv(1024).decode('utf-8')
            if not msg:
                # Jika tidak ada pesan, kemungkinan koneksi terputus
                break

            # Kalau pesan berasal dari user sendiri (misal "Alice: pesan"),
            # jangan print ulang karena sudah ditampilkan saat user kirim
            if msg.startswith(f"{username}:"):
                continue  # Skip supaya gak double print

            print(msg, end='')  # Tampilkan pesan dari server atau user lain

        except:
            print("\n[Disconnected from server]")
            break

def send_messages():
    """Loop untuk input pesan dari user dan kirim ke server"""
    global in_chatroom
    global username

    while True:
        try:
            # Saat sudah masuk room chat, input muncul dengan prefix "You: "
            # Sebelum masuk room chat (di menu), input biasa tanpa prefix
            if in_chatroom:
                msg = input("You: ")
            else:
                msg = input()

            if msg.lower() == 'exit':
                # Kirim perintah exit dan tutup socket
                client.send(msg.encode('utf-8'))
                client.close()
                break

            client.send(msg.encode('utf-8'))  # Kirim pesan ke server

            # Jika sudah di room chat dan pesan bukan command khusus,
            # tampilkan pesan sendiri dengan prefix You:
            if in_chatroom and msg.lower() not in ['exit', 'back', 'menu', 'join', '1', '2', '3']:
                print(f"You: {msg}")

            # Update flag in_chatroom berdasarkan input user
            # Jika user mengetik 'join', berarti masuk room chat
            if msg.lower() == 'join':
                in_chatroom = True
            # Jika user ketik 'back', 'menu', atau 'exit' berarti keluar dari room chat
            elif msg.lower() in ['back', 'menu', 'exit']:
                in_chatroom = False

        except:
            break

# Pertama terima prompt username dari server, lalu input dan kirim username
prompt = client.recv(1024).decode('utf-8')
print(prompt, end='')  # Biasanya tampil "Username: "
username = input().strip()
client.send(username.encode('utf-8'))  # Kirim username ke server

# Terima pesan sambutan dari server dan tampilkan
welcome = client.recv(1024).decode('utf-8')
print(welcome, end='')

# Jalankan thread untuk menerima pesan secara background
threading.Thread(target=receive_messages, daemon=True).start()

# Jalankan fungsi input dan pengiriman pesan di thread utama
send_messages()
