import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients = {}  # {conn: {"username": str, "room": str or None}}
rooms = {}    # {room_name: [conn, ...]}

print(f"[SERVER RUNNING] Listening on {HOST}:{PORT}")

def broadcast(message, room, sender_conn=None):
    for conn in rooms.get(room, []):
        if conn != sender_conn:
            try:
                conn.sendall(message.encode('utf-8'))
            except:
                conn.close()

def send_menu(conn):
    # Kirim menu dengan tanda khusus supaya client bisa deteksi ini menu
    menu_msg = (
        "\n=== MENU UTAMA ===\n"
        "Pilih menu:\n"
        "1. Create room\n"
        "2. Join room\n"
        "3. Exit\n"
        "Masukkan pilihan: "
    )
    conn.send(menu_msg.encode('utf-8'))

def join_room(conn, username):
    while True:
        if rooms:
            room_list = "\n".join(f"- {r}" for r in rooms)
            conn.send(f"\nRoom yang tersedia:\n{room_list}\n\n".encode('utf-8'))
        else:
            conn.send("\nBelum ada room yang tersedia. Silakan buat room terlebih dahulu.\n".encode('utf-8'))
            return False

        conn.send("Masukkan nama room yang ingin dimasuki (atau ketik 'menu' untuk kembali ke menu utama):\n".encode('utf-8'))
        room_name = conn.recv(1024).decode('utf-8').strip()

        if not room_name:
            conn.send("Nama room tidak boleh kosong.\n\n".encode('utf-8'))
            continue

        if room_name.lower() == 'menu':
            return False

        if room_name not in rooms:
            conn.send(f"Room {room_name} tidak tersedia!\n\n".encode('utf-8'))
            continue

        # Tambahkan client ke room
        rooms[room_name].append(conn)
        clients[conn]["room"] = room_name

        # Kirim konfirmasi bergabung dan tanda khusus buat client
        conn.send(f"\n=== Anda telah tergabung di room {room_name} ===\n".encode('utf-8'))

        other_users = [clients[c]["username"] for c in rooms[room_name] if c != conn]
        if other_users:
            conn.send(f"Pengguna lain di room ini: {', '.join(other_users)}\n".encode('utf-8'))
        else:
            conn.send("Anda adalah pengguna pertama di room ini.\n".encode('utf-8'))

        broadcast(f"[{username} telah bergabung ke room {room_name}]", room_name, sender_conn=conn)
        return True

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")
    conn.send("Username: ".encode('utf-8'))

    try:
        username = conn.recv(1024).decode('utf-8').strip()
    except:
        conn.close()
        return

    clients[conn] = {"username": username, "room": None}
    conn.send(f"\nSelamat Datang, {username}!\n".encode('utf-8'))

    while True:
        try:
            send_menu(conn)
            pilihan = conn.recv(1024).decode('utf-8').strip().lower()
            if not pilihan:
                break

            if pilihan in ['1', 'create']:
                conn.send("Masukkan nama room yang ingin dibuat: ".encode('utf-8'))
                room_name = conn.recv(1024).decode('utf-8').strip()
                if not room_name:
                    conn.send("Nama room tidak boleh kosong.\n".encode('utf-8'))
                    continue
                if room_name in rooms:
                    conn.send(f"Room chat {room_name} sudah tersedia.\n".encode('utf-8'))
                    continue

                rooms[room_name] = []

                conn.send(f"\nRoom {room_name} berhasil dibuat.\n".encode('utf-8'))

                # Tampilkan pilihan setelah buat room
                while True:
                    conn.send(
                        "Ketik \n'join' untuk masuk ke room\n"
                        "'back' untuk pindah room chat\n"
                        "'menu' untuk kembali ke menu utama.\n"
                        "Masukkan Pilihan : ".encode('utf-8')
                    )
                    pilihan_lanjut = conn.recv(1024).decode('utf-8').strip().lower()

                    if pilihan_lanjut == 'join':
                        rooms[room_name].append(conn)
                        clients[conn]["room"] = room_name
                        conn.send(f"\n=== Anda telah tergabung di room {room_name} ===\n".encode('utf-8'))

                        other_users = [clients[c]["username"] for c in rooms[room_name] if c != conn]
                        if other_users:
                            conn.send(f"Pengguna lain di room ini: {', '.join(other_users)}\n".encode('utf-8'))
                        else:
                            conn.send("Anda adalah pengguna pertama di room ini.\n".encode('utf-8'))

                        broadcast(f"[{username} telah bergabung ke room {room_name}]", room_name, sender_conn=conn)
                        break

                    elif pilihan_lanjut == 'back':
                        join_room(conn, username)
                        break

                    elif pilihan_lanjut == 'menu':
                        break
                    else:
                        conn.send("Pilihan tidak valid. Ketik 'join', 'back', atau 'menu'.\n".encode('utf-8'))

                if clients[conn]["room"] is None:
                    continue

            elif pilihan in ['2', 'join']:
                success = join_room(conn, username)
                if not success:
                    continue

            elif pilihan in ['3', 'exit']:
                conn.send("Terima kasih telah menggunakan aplikasi chat. Sampai jumpa!\n".encode('utf-8'))
                break

            else:
                conn.send("Pilihan tidak valid, masukkan 1, 2, atau 3.\n".encode('utf-8'))
                continue

            # Setelah join room, mulai loop chat
            while True:
                msg = conn.recv(1024).decode('utf-8').strip()
                if not msg:
                    break

                if msg.lower() == "exit":
                    return

                if msg.lower() == "back":
                    room = clients[conn]["room"]
                    if room and conn in rooms.get(room, []):
                        rooms[room].remove(conn)
                        broadcast(f"[{username} telah meninggalkan room {room}]", room, sender_conn=conn)
                    clients[conn]["room"] = None
                    success = join_room(conn, username)
                    if not success:
                        break
                    continue

                if msg.lower() == "menu":
                    room = clients[conn]["room"]
                    if room and conn in rooms.get(room, []):
                        rooms[room].remove(conn)
                        broadcast(f"[{username} telah meninggalkan room {room}]", room, sender_conn=conn)
                    clients[conn]["room"] = None
                    break

                room = clients[conn]["room"]
                if room:
                    message = f"{username}: {msg}"
                    broadcast(message, room, sender_conn=conn)
                else:
                    conn.send("Anda belum tergabung ke room manapun.\n".encode('utf-8'))

        except Exception as e:
            print(f"[ERROR MENU] {e}")
            break

    room = clients[conn]["room"]
    if room and conn in rooms.get(room, []):
        rooms[room].remove(conn)
        broadcast(f"[{username} telah meninggalkan room {room}]", room, sender_conn=conn)

    del clients[conn]
    conn.close()
    print(f"[DISCONNECTED] {addr}")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()
