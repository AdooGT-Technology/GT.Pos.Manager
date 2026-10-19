# -*- coding: utf-8 -*-
"""Tiny client for the local POS server.

The manager talks to the server over the same JSON socket the gaming clients
use. When the server is not running the call fails fast (short timeout) and the
caller shows a clear message instead of pretending the command worked.
"""

from __future__ import annotations

import json
import os
import socket

DEFAULT_PORT = 54321


def server_address():
    host = os.environ.get("GT_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("GT_SERVER_PORT", DEFAULT_PORT))
    return host, port


class CommandClient:
    def __init__(self, host: str = None, port: int = None, timeout: float = 1.2):
        default_host, default_port = server_address()
        self.host = host or default_host
        self.port = int(port or default_port)
        self.timeout = timeout

    @staticmethod
    def _frame(payload: dict) -> bytes:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return len(body).to_bytes(4, byteorder="big") + body

    @staticmethod
    def _read(sock) -> dict:
        head = sock.recv(4)
        if len(head) == 4:
            size = int.from_bytes(head, byteorder="big")
            if 2 <= size <= 1_000_000:
                body = b""
                while len(body) < size:
                    chunk = sock.recv(min(size - len(body), 8192))
                    if not chunk:
                        break
                    body += chunk
                return json.loads(body.decode("utf-8"))
        return {}

    def send(self, command: str, payload: dict = None) -> tuple[bool, str]:
        message = dict(payload or {})
        message["command"] = command
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.sendall(self._frame(message))
                reply = self._read(sock)
            if not reply:
                return False, "لم يرد السيرفر"
            status = reply.get("status")
            if status in ("ok", "success", "queued"):
                return True, reply.get("message", "تم")
            return False, reply.get("message", "تعذر تنفيذ الأمر")
        except (OSError, ValueError) as error:
            return False, f"السيرفر غير متاح ({error.__class__.__name__})"


def describe(action: str) -> str:
    return {
        "LOCK": "قفل الشاشة",
        "UNLOCK": "فتح الشاشة",
        "RESTART": "إعادة تشغيل",
        "SHUTDOWN": "إيقاف الجهاز",
        "MESSAGE": "إرسال رسالة",
        "WAKE": "تشغيل عن بُعد",
        "UNLOCK_ALL": "فتح كل الأجهزة",
    }.get(action, action)
