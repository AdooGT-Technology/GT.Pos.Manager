import sys
import json
import socket
import threading
from datetime import datetime
from Server.config import Config
from Server.database import DatabaseManager


class POSServer:
    def __init__(self):
        self.db = DatabaseManager()
        self.running = False
        self.clients = {}

    def handle_client(self, conn, addr):
        hostname = str(addr)
        print(f"[+] Client connected: {addr}")
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                try:
                    payload = json.loads(data.decode('utf-8'))
                    self.process_payload(addr, payload)
                except json.JSONDecodeError:
                    print(f"[!] Invalid JSON from {addr}")
        except Exception as e:
            print(f"[-] Client error {addr}: {e}")
        finally:
            print(f"[-] Client disconnected: {addr}")
            if addr in self.clients:
                del self.clients[addr]
            conn.close()

    def process_payload(self, addr, payload):
        hostname = payload.get("hostname", str(addr))
        action = payload.get("action", "stats")

        if action == "stats":
            self.db.execute_query(
                """UPDATE Hosts
                   SET CPU_Usage=?, GPU_Usage=?, RAM_Usage=?, Disk_Usage=?,
                       CPU_Temp=?, GPU_Temp=?
                   WHERE HostName=? OR IPAddress=?""",
                (payload.get("cpu", 0), payload.get("gpu", 0),
                 payload.get("ram", 0), payload.get("disk", 0),
                 payload.get("cpu_temp", 0), payload.get("gpu_temp", 0),
                 hostname, hostname),
                fetch=False
            )
            print(f"[STATS] {hostname}: CPU {payload.get('cpu')}% RAM {payload.get('ram')}%")

        elif action == "register":
            self.db.execute_query(
                """IF NOT EXISTS (SELECT 1 FROM Hosts WHERE HostName=?)
                   INSERT INTO Hosts (HostName, HostType, IPAddress, MACAddress, Status)
                   VALUES (?, 'PC', ?, ?, N'متاح')""",
                (hostname, hostname, payload.get("ip", ""), payload.get("mac", "")),
                fetch=False
            )
            print(f"[REGISTER] {hostname}")

    def start(self):
        self.running = True
        self.db.ensure_database()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((Config.SERVER_HOST, Config.SERVER_PORT))
        server.listen(10)

        print(f"=== GT-POS Server v2.4.0 ===")
        print(f"[✓] Listening on {Config.SERVER_HOST}:{Config.SERVER_PORT}")
        print(f"[i] Waiting for gaming clients...")

        try:
            while self.running:
                conn, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\n[!] Shutting down server...")
        finally:
            self.running = False
            server.close()


def main():
    server = POSServer()
    server.start()


if __name__ == "__main__":
    main()