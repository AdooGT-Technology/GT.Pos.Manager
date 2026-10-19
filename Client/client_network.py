"""
GT-POS Client Network
اتصال العميل بالسيرفر
"""

import socket
import json
import threading
import time


class ClientNetwork:
    """اتصال العميل بالسيرفر"""
    
    def __init__(self, server_host, server_port, host_id, host_number):
        self.server_host = server_host
        self.server_port = server_port
        self.host_id = host_id
        self.host_number = host_number
        self.socket = None
        self.connected = False
        self.running = False
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_connected = None
        self.on_disconnected = None
        self.on_command = None
        self.on_message = None
        self.on_session_update = None
        self.on_time_warning = None
    
    def connect(self):
        """الاتصال بالسيرفر"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            self.running = True
            
            # إرسال رسالة التسجيل
            self._send({
                'type': 'register',
                'host_id': self.host_id,
                'host_number': self.host_number,
                'hostname': getattr(self, 'host_name', ''),
                'ip': getattr(self, 'local_ip', ''),
            })
            
            # بدء الاستقبال
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # بدء نبضات القلب
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            if self.on_connected:
                self.on_connected()
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """قطع الاتصال"""
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.on_disconnected:
            self.on_disconnected()
    
    def _send(self, data):
        """إرسال بيانات"""
        if not self.connected:
            return False
        try:
            message = json.dumps(data).encode('utf-8')
            length = len(message)
            with self.lock:
                self.socket.sendall(length.to_bytes(4, byteorder='big'))
                self.socket.sendall(message)
            return True
        except:
            self.connected = False
            return False
    
    def _receive(self):
        """استقبال بيانات"""
        try:
            length_data = self.socket.recv(4)
            if not length_data:
                return None
            length = int.from_bytes(length_data, byteorder='big')
            
            data = b''
            while len(data) < length:
                chunk = self.socket.recv(min(length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            return None
        except:
            return None
    
    def _receive_loop(self):
        """حلقة الاستقبال"""
        while self.running and self.connected:
            try:
                self.socket.settimeout(5)
                data = self._receive()
                if data is None:
                    continue
                
                self._handle_message(data)
            except Exception:
                if self.running:
                    self.connected = False
                    if self.on_disconnected:
                        self.on_disconnected()
                    break
    
    def _handle_message(self, data):
        """معالجة الرسائل الواردة"""
        msg_type = data.get('type', '')
        
        if msg_type == 'command':
            command = data.get('command', '')
            if self.on_command:
                self.on_command(command, data)
        
        elif msg_type == 'message':
            if self.on_message:
                self.on_message(data.get('text', ''))
        
        elif msg_type == 'session_update':
            if self.on_session_update:
                self.on_session_update(data.get('data', {}))
        
        elif msg_type == 'time_warning':
            if self.on_time_warning:
                self.on_time_warning(
                    data.get('remaining_minutes', 0),
                    data.get('message', '')
                )
        
        elif msg_type == 'server_shutdown':
            self.disconnect()
    
    def _heartbeat_loop(self):
        """حلقة نبضات القلب — الرد قد يحمل أوامر من المدير"""
        while self.running and self.connected:
            time.sleep(8)
            self._send({
                'type': 'heartbeat',
                'hostname': getattr(self, 'host_name', ''),
                'host_id': self.host_id,
                'host_number': self.host_number,
            })
    
    def request_login(self, username, password):
        """طلب تسجيل دخول"""
        self._send({
            'type': 'login_request',
            'username': username,
            'password': password
        })
    
    def send_status(self, status_data):
        """إرسال حالة الجهاز"""
        self._send({
            'type': 'status_update',
            'data': status_data
        })
    
    def auto_reconnect(self, interval=5):
        """إعادة الاتصال تلقائياً"""
        def reconnect_loop():
            while self.running and not self.connected:
                time.sleep(interval)
                if not self.connected:
                    print("Attempting to reconnect...")
                    self.connect()
        
        thread = threading.Thread(target=reconnect_loop, daemon=True)
        thread.start()