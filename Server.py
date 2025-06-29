import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients = {}  # key: conn, value: {"username": str, "room": str or None}
rooms = {}    # key: room_name, value: list of conns

print(f"[SERVER RUNNING] Listening on {HOST}:{PORT}")

def broadcast(message, room, sender_conn=None):
    for conn in rooms.get(room, []):
        if conn != sender_conn:
            try:
                conn.sendall(message.encode('utf-8'))
            except:
                conn.close()

def send_menu(conn):
    conn.send("Pilih menu:\n1. Create room\n2. Join room\nMasukkan pilihan: ".encode('utf-8'))

def join_room(conn, username):
    while True:
        if rooms:
            room_list = "\n".join(f"- {r}" for r in rooms)
            conn.send(f"Room yang tersedia:\n{room_list}\n\n".encode('utf-8'))
        else:
            conn.send("Belum ada room yang tersedia. Silakan buat room terlebih dahulu.\n".encode('utf-8'))
            return False  # Kembali ke menu utama karena tidak ada room

        conn.send("Masukkan nama room yang ingin dimasuki (atau ketik 'back' untuk kembali ke menu utama):\n".encode('utf-8'))
        room_name = conn.recv(1024).decode('utf-8').strip()
        if not room_name:
            conn.send("Nama room tidak boleh kosong.\n\n".encode('utf-8'))
            continue
        if room_name.lower() == 'back':
            return False  # Kembali ke menu utama

        if room_name not in rooms:
            conn.send(f"Room {room_name} tidak tersedia!\n\n".encode('utf-8'))
            continue

        rooms[room_name].append(conn)
        clients[conn]["room"] = room_name
        conn.send(f"{username} bergabung ke dalam room {room_name}\n".encode('utf-8'))

        # Kirim daftar user lain di room (kecuali dirinya)
        other_users = [clients[c]["username"] for c in rooms[room_name] if c != conn]
        if other_users:
            conn.send(f"Pengguna lain di room ini: {', '.join(other_users)}\n".encode('utf-8'))
        else:
            conn.send("Anda adalah pengguna pertama di room ini.\n".encode('utf-8'))

        # Broadcast notif user baru join (kecuali ke diri sendiri)
        broadcast(f"[{username} telah bergabung ke room]", room_name, sender_conn=conn)

        return True  # Berhasil masuk room

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")
    conn.send("Username: ".encode('utf-8'))
    try:
        username = conn.recv(1024).decode('utf-8').strip()
    except:
        conn.close()
        return
    clients[conn] = {"username": username, "room": None}
    conn.send(f"Selamat Datang, {username}!\n".encode('utf-8'))

    while True:  # MENU UTAMA LOOP
        try:
            send_menu(conn)
            pilihan = conn.recv(1024).decode('utf-8').strip().lower()
            if not pilihan:
                break

            # CREATE ROOM
            if pilihan == '1' or pilihan == 'create':
                conn.send("Masukkan nama room yang ingin dibuat: ".encode('utf-8'))
                room_name = conn.recv(1024).decode('utf-8').strip()
                if not room_name:
                    conn.send("Nama room tidak boleh kosong.\n".encode('utf-8'))
                    continue
                if room_name in rooms:
                    conn.send(f"Room chat {room_name} sudah tersedia.\n".encode('utf-8'))
                    continue

                rooms[room_name] = []
                conn.send(f"Room {room_name} berhasil dibuat.\n".encode('utf-8'))

                while True:
                    conn.send("Ketik \n'join' untuk masuk ke room\n'back' untuk pindah room chat\n'menu' untuk kembali ke menu utama.\n".encode('utf-8'))
                    conn.send("Masukkan Pilihan : ".encode('utf-8'))
                    pilihan_lanjut = conn.recv(1024).decode('utf-8').strip().lower()
                    if pilihan_lanjut == 'join':
                        rooms[room_name].append(conn)
                        clients[conn]["room"] = room_name
                        conn.send(f"Anda telah tergabung di room {room_name}.\n".encode('utf-8'))

                        # Kirim daftar user lain di room (kecuali dirinya)
                        other_users = [clients[c]["username"] for c in rooms[room_name] if c != conn]
                        if other_users:
                            conn.send(f"Pengguna lain di room ini: {', '.join(other_users)}\n".encode('utf-8'))
                        else:
                            conn.send("Anda adalah pengguna pertama di room ini.\n".encode('utf-8'))

                        broadcast(f"[{username} telah bergabung ke room]", room_name, sender_conn=conn)
                        break
                    elif pilihan_lanjut == 'menu' or pilihan_lanjut == 'back':
                        break
                    else:
                        conn.send("Pilihan tidak valid. Ketik 'join', 'back', atau 'menu'.\n".encode('utf-8'))

                if clients[conn]["room"] is None:
                    continue  # Kembali ke menu utama

            # JOIN ROOM
            elif pilihan == '2' or pilihan == 'join':
                success = join_room(conn, username)
                if not success:
                    continue  # kembali ke menu utama jika tidak berhasil masuk room

            else:
                conn.send("Pilihan tidak valid, masukkan 1 atau 2.\n".encode('utf-8'))
                continue

            # CHAT LOOP setelah masuk room
            while True:
                msg = conn.recv(1024).decode('utf-8').strip()
                if not msg:
                    break

                if msg.lower() == "exit":
                    return  # keluar koneksi

                if msg.lower() == "back":
                    # Keluar dari room, hapus dari list
                    room = clients[conn]["room"]
                    if room and conn in rooms.get(room, []):
                        rooms[room].remove(conn)
                        broadcast(f"[{username} telah meninggalkan room]", room, sender_conn=conn)
                        if len(rooms[room]) == 0:
                            del rooms[room]
                    clients[conn]["room"] = None

                    # langsung masuk ke menu join room (pilihan 2)
                    success = join_room(conn, username)
                    if not success:
                        break  # jika gagal join room (misal ketik back), kembali ke menu utama

                    continue  # kembali ke chat loop setelah berhasil join room

                if msg.lower() == "menu":
                    # Keluar dari room, hapus dari list
                    room = clients[conn]["room"]
                    if room and conn in rooms.get(room, []):
                        rooms[room].remove(conn)
                        broadcast(f"[{username} telah meninggalkan room]", room, sender_conn=conn)
                        if len(rooms[room]) == 0:
                            del rooms[room]
                    clients[conn]["room"] = None
                    break  # kembali ke menu utama

                room = clients[conn]["room"]
                if room:
                    message = f"{username}: {msg}"
                    broadcast(message, room, sender_conn=conn)
                else:
                    conn.send("Anda belum tergabung ke room manapun.\n".encode('utf-8'))

        except Exception as e:
            print(f"[ERROR MENU] {e}")
            break

    # Cleanup saat keluar permanen
    room = clients[conn]["room"]
    if room and conn in rooms.get(room, []):
        rooms[room].remove(conn)
        broadcast(f"[{username} telah meninggalkan room]", room, sender_conn=conn)
        if len(rooms[room]) == 0:
            del rooms[room]

    del clients[conn]
    conn.close()
    print(f"[DISCONNECTED] {addr}")


while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()


#coba push github
#testetstetst