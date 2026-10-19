# -*- coding: utf-8 -*-
"""
GT-POS Manager - Server Network Listener
Version: 1.0.2
"""

import socket
import threading
import json
import logging
from Server.config import Config
from Server.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkServer:
    def __init__(self, host=Config.SERVER_HOST, port=Config.SERVER_PORT):
        self.host = host
        self.port = port
        self.db = DatabaseManager()
        self.server_socket = None
        self.is_running = False
        self.clients = {}

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self.is_running = True
            logging.info(f"🟢 تم تشغيل سيرفر الشبكة على {self.host}:{self.port}")
            
            accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            accept_thread.start()
            return True
        except Exception as e:
            logging.error(f"🔴 فشل تشغيل السيرفر على المنفذ {self.port}: {e}")
            return False

    def _accept_connections(self):
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                ip = address[0]
                logging.info(f"🤝 اتصال جديد من: {ip}")
                
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, ip),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.is_running:
                    logging.error(f"خطأ أثناء استقبال الاتصالات: {e}")
                break

    def _handle_client(self, client_socket, ip):
        self.db.update_host_ping(ip)
        
        while self.is_running:
            try:
                data = client_socket.recv(Config.BUFFER_SIZE)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    response = self._process_command(message, ip)
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    client_socket.send(json.dumps({"status": "error", "message": "Invalid JSON"}).encode('utf-8'))

            except Exception as e:
                logging.error(f"خطأ في الاتصال مع {ip}: {e}")
                break

        client_socket.close()

    def _process_command(self, msg, ip):
        cmd = msg.get("command")
        
        if cmd == "PING":
            self.db.update_host_ping(ip)
            return {"status": "ok", "message": "PONG"}
        
        elif cmd == "LOGIN_MEMBER":
            user = msg.get("username")
            password = msg.get("password")
            member = self.db.authenticate_member(user, password)
            if member:
                return {"status": "success", "member": member}
            return {"status": "fail", "message": "بيانات الدخول غير صحيحة"}

        elif cmd == "GET_STATUS":
            stats = self.db.get_dashboard_stats()
            return {"status": "success", "data": stats}

        return {"status": "unknown_command"}

    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        logging.info("🔴 تم إيقاف السيرفر.")