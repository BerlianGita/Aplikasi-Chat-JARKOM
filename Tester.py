import socket
import threading
import ipaddress

class Tester:
    def __init__(self, port, base_network=None, workers=50, timeout=0.3):
        self.port = port
        self.timeout = timeout
        self.found_ip = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.workers = workers
        if base_network:
            self.network = ipaddress.ip_network(base_network, strict=False)
        else:
            self.network = self.detect_local_network()

    def detect_local_network(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "192.168.1.100"  # fallback

        net = ipaddress.ip_network(local_ip + '/24', strict=False)
        print(f"[INFO] Detected local network: {net}")
        return net

    def is_server_alive(self, ip):
        if self.stop_event.is_set():
            return False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((str(ip), self.port))
                return True
        except:
            return False

    def worker(self, ips):
        for ip in ips:
            if self.stop_event.is_set():
                return
            if self.is_server_alive(ip):
                with self.lock:
                    self.found_ip = str(ip)
                    self.stop_event.set()
                print(f"\n[✓] Server ditemukan di: {ip}:{self.port}")
                return

    def find_server_ip(self):
        all_hosts = list(self.network.hosts())
        chunk = len(all_hosts) // self.workers + 1

        threads = []
        for i in range(self.workers):
            ips = all_hosts[i*chunk:(i+1)*chunk]
            t = threading.Thread(target=self.worker, args=(ips,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if not self.found_ip:
            print("\n[!] Server tidak ditemukan di jaringan.")
        return self.found_ip


def get_server_ip(port=12345):
    tester = Tester(port=port)
    return tester.find_server_ip()


if __name__ == "__main__":
    ip = get_server_ip()
    if ip:
        print(f"[INFO] IP Server: {ip}")
    else:
        print("[INFO] Gagal menemukan server.")
