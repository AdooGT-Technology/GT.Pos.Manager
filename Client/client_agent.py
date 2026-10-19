import json
import time
import socket
import platform
import sys

try:
    from telemetry import collect
except ImportError:  # running as a module
    from Client.telemetry import collect


class GamingClientAgent:
    def __init__(self, server_host="localhost", server_port=54321):
        self.server_host = server_host
        self.server_port = server_port
        self.hostname = platform.node()
        self.running = False

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def get_mac(self):
        try:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                           for ele in range(0, 8*6, 8)][::-1])
            return mac
        except:
            return "00:00:00:00:00:00"

    def collect_stats(self):
        payload = collect()
        payload.update({
            "action": "stats",
            "hostname": self.hostname,
            "timestamp": time.time(),
        })
        return payload

    def register(self):
        return {
            "action": "register",
            "hostname": self.hostname,
            "ip": self.get_local_ip(),
            "mac": self.get_mac()
        }

    def send(self, payload):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((self.server_host, self.server_port))
                s.sendall(json.dumps(payload).encode('utf-8'))
                return True
        except Exception as e:
            print(f"[!] Send error: {e}")
            return False

    def run(self):
        self.running = True
        print("=== GT-POS Client Agent ===")
        print(f"[i] Hostname: {self.hostname}")
        print(f"[i] Server: {self.server_host}:{self.server_port}")
        print("[i] Starting telemetry loop...")

        self.send(self.register())

        while self.running:
            stats = self.collect_stats()
            if not self.send(stats):
                print("[!] Failed to send stats, retrying in 10s...")
                time.sleep(10)
            else:
                time.sleep(5)


def main():
    server_host = "localhost"
    if len(sys.argv) > 1:
        server_host = sys.argv[1]

    agent = GamingClientAgent(server_host=server_host)
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n[!] Agent stopped.")


if __name__ == "__main__":
    main()