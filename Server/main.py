# -*- coding: utf-8 -*-
"""GT-POS socket server.

Clients send telemetry; the manager sends commands. Every request gets a JSON
reply so the other side can tell success from silence.
"""

from __future__ import annotations

import json
import logging
import socket
import threading

from Server.config import Config
from Server.database import DatabaseManager

MAX_FRAME = 1_000_000


def _read_message(conn):
    """Read one message.

    Clients (and the manager) send a 4-byte big-endian length followed by JSON.
    Plain JSON without the prefix is still accepted for older builds.
    """
    head = conn.recv(4)
    if not head:
        return None
    if len(head) == 4:
        size = int.from_bytes(head, byteorder="big")
        if 2 <= size <= MAX_FRAME:
            payload = b""
            while len(payload) < size:
                chunk = conn.recv(min(size - len(payload), 8192))
                if not chunk:
                    break
                payload += chunk
            try:
                return json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
    # Legacy raw JSON: keep reading until it parses.
    buffer = head
    for _ in range(8):
        try:
            return json.loads(buffer.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            more = conn.recv(Config.BUFFER_SIZE)
            if not more:
                return None
            buffer += more
    return None


def _write_message(conn, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    conn.sendall(len(body).to_bytes(4, byteorder="big") + body)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("server")


class POSServer:
    def __init__(self):
        self.db = DatabaseManager()
        self.running = False
        self.clients = {}
        self.queue = {}
        self._lock = threading.Lock()

    # ── socket loop ──────────────────────────────────────────────────────
    def handle_client(self, conn, addr):
        label = str(addr)
        log.info("client connected: %s", label)
        conn.settimeout(120)
        try:
            while self.running:
                payload = _read_message(conn)
                if payload is None:
                    break
                reply = self.process_payload(addr, payload)
                if reply is not None:
                    self._reply(conn, reply)
        except (OSError, socket.timeout) as error:
            log.debug("client %s closed: %s", label, error)
        finally:
            with self._lock:
                self.clients.pop(addr, None)
            try:
                conn.close()
            except OSError:
                pass
            log.info("client disconnected: %s", label)

    @staticmethod
    def _reply(conn, payload: dict):
        try:
            _write_message(conn, payload)
        except OSError:
            pass

    # ── request handling ─────────────────────────────────────────────────
    def process_payload(self, addr, payload: dict):
        command = payload.get("command") or payload.get("type")
        action = payload.get("action") or payload.get("type")

        if command == "PING":
            return {"status": "ok", "message": "PONG"}

        if command == "GET_STATUS":
            return {"status": "success", "data": self.db.get_dashboard_stats()}

        if command == "LOGIN_MEMBER":
            member = self.db.authenticate_member(
                payload.get("username", ""), payload.get("password", "")
            )
            if member:
                return {"status": "success", "member": member}
            return {"status": "fail", "message": "بيانات الدخول غير صحيحة"}

        if command and command.startswith("DEVICE_"):
            return self._device_command(payload)

        if command in ("GET_COMMANDS", "heartbeat"):
            host = payload.get("host") or payload.get("hostname") or str(addr[0])
            return {
                "status": "ok",
                "type": "commands",
                "commands": [dict(item, type="command") for item in self._take_commands(host)],
            }

        if command in ("login_request",):
            member = self.db.authenticate_member(
                payload.get("username", ""), payload.get("password", "")
            )
            return {"type": "login_result", "status": bool(member), "member": member}

        if command == "status_update":
            data = payload.get("data") or {}
            data.setdefault("ip", addr[0])
            self._save_telemetry(data)
            return {"status": "ok"}

        if command in ("register", "stats"):
            if command == "register":
                self._register_host(dict(payload, ip=addr[0]))
            else:
                self._save_telemetry(dict(payload, ip=addr[0]))
            return {"status": "ok", "type": "registered" if command == "register" else "ack"}

        if action == "stats":
            self._save_telemetry(payload)
            return {"status": "ok"}

        if action == "register":
            self._register_host(payload)
            return {"status": "ok", "message": "registered"}

        if action == "heartbeat":
            host = payload.get("hostname", "")
            return {"status": "ok", "commands": self._take_commands(host)}

        return {"status": "unknown_command"}

    def _device_command(self, payload: dict):
        command = payload.get("command", "")
        kind = command.replace("DEVICE_", "", 1)
        targets = payload.get("hosts")
        if not targets:
            targets = [payload.get("host")] if payload.get("host") else []
        targets = [str(target) for target in targets if target]

        message = {
            "command": kind,
            "text": payload.get("text", ""),
            "game": payload.get("game", ""),
            "exe": payload.get("exe", ""),
            "issued_by": payload.get("issued_by", "manager"),
        }
        with self._lock:
            if targets:
                for host in targets:
                    self.queue.setdefault(host, []).append(message)
            else:
                self.queue.setdefault("*", []).append(message)

        self.db.log_activity(
            f"أمر {kind}", "، ".join(targets) or "كل الأجهزة", "device"
        )
        log.info("command %s → %s", kind, targets or "all")
        return {
            "status": "queued",
            "message": f"أُرسل إلى {len(targets) or 1} جهاز",
            "targets": targets,
        }

    def _take_commands(self, host: str):
        with self._lock:
            for key in (host, "*"):
                if self.queue.get(key):
                    return self.queue.pop(key)
        return []

    # ── persistence ──────────────────────────────────────────────────────
    def _resolve_host(self, payload: dict) -> str:
        if payload.get("hostname"):
            return str(payload["hostname"])
        if payload.get("host"):
            return str(payload["host"])
        host_number = payload.get("host_number")
        host_id = payload.get("host_id")
        if host_number is not None or host_id is not None:
            rows = self.db.execute_query(
                "SELECT TOP 1 HostName FROM Hosts WHERE HostNumber = ? OR HostId = ?",
                (host_number, host_id),
            )
            if rows and rows[0].get("HostName"):
                return str(rows[0]["HostName"])
            return f"PC-{int(host_number or host_id or 0):02d}"
        return ""

    def _save_telemetry(self, payload: dict):
        hostname = self._resolve_host(payload) or payload.get("ip") or ""
        if not hostname:
            return
        self.db.execute_query(
            """UPDATE Hosts SET CPU_Usage=?, GPU_Usage=?, RAM_Usage=?, Disk_Usage=?,
                   CPU_Temp=?, GPU_Temp=?, GPU_Name=?
               WHERE HostName=? OR IPAddress=?""",
            (
                payload.get("cpu", 0), payload.get("gpu", 0),
                payload.get("ram", 0), payload.get("disk", 0),
                payload.get("cpu_temp", 0), payload.get("gpu_temp", 0),
                payload.get("gpu_name", ""),
                hostname, payload.get("ip", hostname),
            ),
            fetch=False,
        )

    def _register_host(self, payload: dict):
        hostname = self._resolve_host(payload) or str(payload.get("ip", ""))
        if not hostname:
            return
        self.db.execute_query(
            """IF NOT EXISTS (SELECT 1 FROM Hosts WHERE HostName = ?)
                   INSERT INTO Hosts (HostName, HostType, IPAddress, MACAddress, Status)
                   VALUES (?, 'PC', ?, ?, N'متاح')
               ELSE
                   UPDATE Hosts SET IPAddress=?, MACAddress=?, IsActive=1 WHERE HostName=?""",
            (
                hostname, hostname, payload.get("ip", ""), payload.get("mac", ""),
                payload.get("ip", ""), payload.get("mac", ""), hostname,
            ),
            fetch=False,
        )
        log.info("registered %s", hostname)

    # ── lifecycle ────────────────────────────────────────────────────────
    def start(self):
        self.running = True
        self.db.ensure_database()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((Config.SERVER_HOST, Config.SERVER_PORT))
        server.listen(50)
        log.info("GT-POS server listening on %s:%s", Config.SERVER_HOST, Config.SERVER_PORT)

        try:
            while self.running:
                conn, addr = server.accept()
                with self._lock:
                    self.clients[addr] = conn
                threading.Thread(
                    target=self.handle_client, args=(conn, addr), daemon=True
                ).start()
        except KeyboardInterrupt:
            log.info("shutting down")
        finally:
            self.running = False
            try:
                server.close()
            except OSError:
                pass


def main():
    POSServer().start()


if __name__ == "__main__":
    main()
