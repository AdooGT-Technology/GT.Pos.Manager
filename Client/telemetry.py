# -*- coding: utf-8 -*-
"""Telemetry collected on the gaming PC.

One place used by both the tray client and the headless agent, so the manager
always receives the same fields: CPU, GPU, VRAM, RAM, disk and network.
Static values (GPU name, disk size/health, link speed) are cached because they
change rarely and some of them are slow to query.
"""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None
else:  # prime the CPU sampler so the first reading is not always zero
    psutil.cpu_percent(interval=0.1)

_cache: dict = {}
_cache_time: dict = {}
_state = {"last_net": None, "last_time": None}


def _cached(key: str, ttl: float, producer):
    now = time.monotonic()
    if key in _cache and (now - _cache_time.get(key, 0)) < ttl:
        return _cache[key]
    try:
        value = producer()
    except Exception:
        value = _cache.get(key)
    _cache[key] = value
    _cache_time[key] = now
    return value


def _system_drive() -> str:
    return os.environ.get("SystemDrive", "C:") + "\\" if os.name == "nt" else "/"


def _gpu_info() -> dict:
    def read():
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu,"
             "memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=4,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        first = result.stdout.strip().splitlines()[0]
        parts = [part.strip() for part in first.split(",")]
        if len(parts) < 5:
            return {}
        return {
            "name": parts[0],
            "usage": _float(parts[1]),
            "temp": _float(parts[2]),
            "vram_used": round(_float(parts[3]) / 1024, 2),
            "vram_total": round(_float(parts[4]) / 1024, 2),
        }
    return _cached("gpu", 10.0, read) or {}


def _float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _cpu_temp() -> float:
    def read():
        if psutil is None or not hasattr(psutil, "sensors_temperatures"):
            return 0.0
        sensors = psutil.sensors_temperatures() or {}
        for name in ("coretemp", "k10temp", "cpu_thermal", "zenpower", "acpitz"):
            for entry in sensors.get(name, []):
                if entry.current:
                    return float(entry.current)
        for entries in sensors.values():
            for entry in entries:
                if entry.current:
                    return float(entry.current)
        return 0.0
    return _cached("cpu_temp", 5.0, read) or 0.0


def _ram_speed() -> int:
    def read():
        if os.name != "nt":
            return 0
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_PhysicalMemory | Select-Object -First 1 "
             "-ExpandProperty Speed)"],
            capture_output=True, text=True, timeout=6,
        )
        return int(_float(result.stdout.strip().splitlines()[0]) if result.stdout.strip() else 0)
    return int(_cached("ram_speed", 600.0, read) or 0)


def _disk_health() -> str:
    def read():
        if os.name != "nt":
            return ""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-PhysicalDisk | Select-Object -First 1 -ExpandProperty HealthStatus)"],
            capture_output=True, text=True, timeout=8,
        )
        text = (result.stdout or "").strip().upper()
        return text if text in ("HEALTHY", "WARNING", "UNHEALTHY") else ""
    return _cached("disk_health", 300.0, read) or ""


def _network() -> dict:
    if psutil is None:
        return {}
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        return {}

    active = None
    for name, entries in addrs.items():
        for entry in entries:
            if getattr(entry, "family", None) == socket.AF_INET and entry.address == local_ip:
                active = name
                break
        if active:
            break

    if active is None:  # fall back to any wired/wireless adapter that is up
        for name, item in stats.items():
            if not getattr(item, "isup", False) or name.lower().startswith("lo"):
                continue
            for entry in addrs.get(name, []):
                if getattr(entry, "family", None) == socket.AF_INET and not entry.address.startswith("127."):
                    active = name
                    break
            if active:
                break

    speed = 0
    if active and active in stats:
        speed = int(getattr(stats[active], "speed", 0) or 0)
    if speed <= 0:
        speed = max((int(getattr(item, "speed", 0) or 0) for item in stats.values()), default=0)

    counters = psutil.net_io_counters()
    sent_gb = counters.bytes_sent / (1024 ** 3)
    recv_gb = counters.bytes_recv / (1024 ** 3)
    return {
        "net_name": active or "",
        "net_speed": speed,
        "net_upload": round(sent_gb, 3),
        "net_download": round(recv_gb, 3),
        "net_total": round(sent_gb + recv_gb, 3),
    }


def _disk() -> dict:
    def read():
        drive = _system_drive()
        usage = shutil.disk_usage(drive)
        return {
            "total": round(usage.total / (1024 ** 3), 1),
            "percent": round(usage.used / usage.total * 100, 1) if usage.total else 0.0,
        }
    info = _cached("disk", 60.0, read) or {}
    return {
        "disk": info.get("percent", 0.0),
        "disk_total": info.get("total", 0.0),
        "disk_health": _disk_health(),
    }


def collect(basic_only: bool = False) -> dict:
    """Return the telemetry payload expected by Server/main.py."""
    payload = {
        "hostname": platform.node(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "mac": _mac(),
        "uptime": int(time.monotonic()),
        "cpu": 0.0, "cpu_temp": 0.0, "gpu": 0.0, "gpu_temp": 0.0,
        "gpu_name": "", "vram_used": 0.0, "vram_total": 0.0,
        "ram": 0.0, "ram_total": 0.0, "ram_speed": 0,
        "disk": 0.0, "disk_total": 0.0, "disk_health": "",
        "net_name": "", "net_speed": 0,
        "net_upload": 0.0, "net_download": 0.0, "net_total": 0.0,
    }

    if psutil is not None:
        memory = psutil.virtual_memory()
        payload["cpu"] = round(psutil.cpu_percent(interval=None), 1)
        payload["ram"] = round(memory.percent, 1)
        payload["ram_total"] = round(memory.total / (1024 ** 3), 1)
        payload["cpu_temp"] = round(_cpu_temp(), 1)

    payload.update(_disk())
    if basic_only:
        return payload

    payload["ram_speed"] = _ram_speed()
    gpu = _gpu_info()
    payload.update({
        "gpu": gpu.get("usage", 0.0),
        "gpu_temp": gpu.get("temp", 0.0),
        "gpu_name": gpu.get("name", ""),
        "vram_used": gpu.get("vram_used", 0.0),
        "vram_total": gpu.get("vram_total", 0.0),
    })
    payload.update(_network())
    return payload


def _mac() -> str:
    import uuid
    node = uuid.getnode()
    return ":".join(f"{(node >> shift) & 0xff:02X}" for shift in range(40, -1, -8))
