import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Aplikasi Chat")

        self.client = None
        self.stop_thread = False
        self.username = ""

        # Area tampilan chat (readonly)
        self.chat_area = scrolledtext.ScrolledText(master, state='disabled', wrap=tk.WORD, width=100, height=20)
        self.chat_area.pack(padx=10, pady=10)

        # Entry input pesan
        self.msg_entry = tk.Entry(master, width=50)
        self.msg_entry.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10))
        self.msg_entry.bind("<Return>", self.send_message)

        # Tombol kirim
        self.send_button = tk.Button(master, text="Kirim", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=10, pady=(0, 10))

        self.login()

    def login(self):
        # Input username
        self.username = simpledialog.askstring("Username", "Masukkan Username Anda:", parent=self.master)
        if not self.username:
            messagebox.showerror("Error", "Username tidak boleh kosong!")
            self.master.destroy()
            return

        HOST = '127.0.0.1'
        PORT = 12345

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))
        except Exception as e:
            messagebox.showerror("Koneksi Gagal", f"Gagal terhubung ke server:\n{e}")
            self.master.destroy()
            return

        prompt = self.client.recv(1024).decode('utf-8')
        if prompt.strip().lower() == 'username:':
            self.client.send(self.username.encode('utf-8'))

        welcome_msg = self.client.recv(1024).decode('utf-8')
        self.append_chat(welcome_msg)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def append_chat(self, msg):
        # Tampilkan pesan ke area chat, ganti nama sendiri dengan 'You'
        self.chat_area.config(state='normal')
        if msg.startswith(f"{self.username}:"):
            msg = msg.replace(f"{self.username}:", "You:", 1)
        self.chat_area.insert(tk.END, msg + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def receive_messages(self):
        while not self.stop_thread:
            try:
                msg = self.client.recv(1024).decode('utf-8')
                if not msg:
                    self.append_chat("[Terputus dari server]")
                    break
                self.append_chat(msg)
            except:
                self.append_chat("[Koneksi terputus]")
                break

    def send_message(self, event=None):
        msg = self.msg_entry.get().strip()
        if msg == "":
            return
        try:
            self.client.send(msg.encode('utf-8'))

            # Tambahkan pesan sendiri secara lokal
            if msg.lower() not in ["exit"]:
                self.append_chat(f"You: {msg}")

            if msg.lower() == "exit":
                self.stop_thread = True
                self.client.close()
                self.master.destroy()

        except:
            messagebox.showerror("Kesalahan", "Gagal mengirim pesan.")
            self.stop_thread = True
            self.master.destroy()

        self.msg_entry.delete(0, tk.END)

def main():
    root = tk.Tk()
    client_gui = ChatClientGUI(root)

    def on_closing():
        client_gui.stop_thread = True
        if client_gui.client:
            try:
                client_gui.client.send("exit".encode('utf-8'))
                client_gui.client.close()
            except:
                pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
