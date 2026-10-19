# -*- coding: utf-8 -*-
"""Thin data layer for the manager.

Every page asks this module for rows. It keeps a short-lived cache so switching
pages does not open a database connection per widget, and falls back to stable
demo rows when the database is not reachable (so the UI stays usable).
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta

try:
    from Server.database import DatabaseManager
except Exception:  # pragma: no cover - pyodbc may be absent on dev machines
    DatabaseManager = None

CACHE_TTL = 4.0
DEMO = "demo"


def _now():
    return time.monotonic()


class Data:
    def __init__(self, db=None):
        if db is None and DatabaseManager is not None:
            try:
                db = DatabaseManager()
            except Exception:
                db = None
        self.db = db
        self._cache = {}
        self._live = None
        self._live_checked = 0.0
        self._db_down_until = 0.0
        self._rng = random.Random(7)

    # ── low level ────────────────────────────────────────────────────────
    def query(self, sql: str, params=None, ttl: float = CACHE_TTL, key: str = None):
        cache_key = key or f"{sql}|{params}"
        cached = self._cache.get(cache_key)
        if cached and (_now() - cached[0]) < ttl:
            return cached[1]
        rows = []
        if self.db is not None and _now() >= self._db_down_until:
            try:
                rows = self.db.execute_query(sql, params) or []
            except Exception:
                rows = []
            if not self._live and rows == []:
                # The driver refused; stop hammering it for a short while.
                self._db_down_until = _now() + 20.0
        self._cache[cache_key] = (_now(), rows)
        return rows

    def execute(self, sql: str, params=None) -> bool:
        if self.db is None or _now() < self._db_down_until:
            return False
        try:
            ok = bool(self.db.execute_query(sql, params, fetch=False))
        except Exception:
            ok = False
        self._cache.clear()
        return ok

    @property
    def settings(self):
        """Settings catalogue (tax, currency, layout…) shared by the pages."""
        store = getattr(self, "_settings_store", None)
        if store is None:
            from Manager.settings_store import SettingsStore
            store = SettingsStore(self)
            self._settings_store = store
        return store

    def invalidate(self):
        self._cache.clear()

    @property
    def live(self) -> bool:
        if self._live is None or (_now() - self._live_checked) > 30:
            try:
                self._live = bool(self.db and self.db.test_connection())
            except Exception:
                self._live = False
            self._live_checked = _now()
            if not self._live:
                self._db_down_until = _now() + 20.0
        return self._live

    # ── hosts ────────────────────────────────────────────────────────────
    def hosts(self, ttl: float = 3.0):
        rows = self.query(
            "SELECT HostId, HostName, HostNumber, IPAddress, MACAddress, Status,"
            " CPU_Usage, GPU_Usage, RAM_Usage, RAM_Total, RAM_Speed, Disk_Usage,"
            " Disk_Total, Disk_Health, CPU_Temp, GPU_Temp, GPU_Name, VRAM_Used,"
            " VRAM_Total, Net_Name, Net_Speed, Net_Upload, Net_Download, Net_Total,"
            " UptimeMinutes, CurrentUser, HostGroup FROM Hosts WHERE IsActive = 1"
            " ORDER BY HostNumber",
            ttl=ttl, key="hosts",
        )
        return rows or self.demo_hosts()

    def demo_hosts(self):
        if "demo_hosts" in self.__dict__:
            return self._demo_hosts
        gpus = ["RTX 4070", "RTX 4060 Ti", "RX 7800 XT", "RTX 3080", "RTX 3060"]
        names = ["سالم", "عبدالله", "يوسف", "ماجد", "طلال", "خالد", "", "", "فهد", "", "ناصر", ""]
        states = ["مشغول", "متاح", "مشغول", "متاح", "مشغول", "متاح", "مشغول", "متاح",
                  "متاح", "مشغول", "متاح", "متاح"]
        rows = []
        for index in range(1, 19):
            busy = states[(index - 1) % len(states)] == "مشغول"
            vram_total = 12 if index % 3 else 8
            gpu_use = self._rng.randint(40, 88) if busy else self._rng.randint(0, 4)
            net_speed = 1000 if index % 4 else 100
            upload = round(self._rng.uniform(0.4, 9.5) if busy else 0.1, 2)
            download = round(self._rng.uniform(2.0, 48.0) if busy else 0.4, 2)
            rows.append({
                "HostId": index,
                "HostName": f"PC-{index:02d}",
                "HostGroup": "غرف VIP" if index in (1, 2, 13) else "أجهزة PC",
                "HostNumber": index,
                "IPAddress": f"192.168.1.{100 + index}",
                "MACAddress": f"5C:60:BA:0A:{index:02X}:11",
                "Status": "مشغول" if busy else "متاح",
                "CurrentUser": names[(index - 1) % len(names)] if busy else "",
                "CPU_Usage": self._rng.randint(18, 62) if busy else self._rng.randint(2, 9),
                "GPU_Usage": gpu_use,
                "RAM_Usage": self._rng.randint(40, 78) if busy else self._rng.randint(18, 30),
                "RAM_Total": 32,
                "RAM_Speed": 3200,
                "Disk_Usage": self._rng.randint(42, 66),
                "Disk_Total": 1000,
                "Disk_Health": "HEALTHY",
                "CPU_Temp": self._rng.randint(48, 71) if busy else self._rng.randint(35, 44),
                "GPU_Temp": self._rng.randint(55, 79) if busy else self._rng.randint(33, 42),
                "GPU_Name": gpus[index % len(gpus)],
                "VRAM_Used": round(vram_total * gpu_use / 100 * 0.9, 1),
                "VRAM_Total": vram_total,
                "Net_Name": "Ethernet",
                "Net_Speed": 0 if index == 12 else net_speed,
                "Net_Upload": upload,
                "Net_Download": download,
                "Net_Total": round(upload + download, 2),
                "UptimeMinutes": self._rng.randint(40, 380) if busy else 0,
            })
        self._demo_hosts = rows
        return rows

    def host(self, host_id: int):
        for row in self.hosts():
            if int(row.get("HostId") or 0) == int(host_id):
                return row
        return None

    # ── members ──────────────────────────────────────────────────────────
    def members(self, ttl: float = 10.0):
        rows = self.query(
            "SELECT MemberId, Username, FullName, Phone, Balance, Points, MemberType,"
            " MemberGroup, PurchasedMinutes, IsActive"
            " FROM Members ORDER BY MemberId DESC",
            ttl=ttl, key="members",
        )
        return rows or self.demo_members()

    def demo_members(self):
        base = [
            ("ahmed99", "أحمد محمد", "0551234567", 150.0, 320, "VIP"),
            ("khalid_x", "خالد عبدالله", "0559876543", 25.0, 80, "عادي"),
            ("fahad2", "فهد سعد", "0501112233", 0.0, 12, "عادي"),
            ("noura.g", "نورة الغامدي", "0533445566", 320.5, 640, "VIP"),
            ("m_alzahrani", "مازن الزهراني", "0566778899", 64.0, 150, "عادي"),
            ("sara_99", "سارة القحطاني", "0544556677", 12.0, 45, "eSports"),
        ]
        return [
            {"MemberId": i + 1, "Username": u, "FullName": n, "Phone": p,
             "Balance": b, "Points": pts, "MemberType": t, "MemberGroup": t,
             "PurchasedMinutes": (60 if i == 0 else 0), "IsActive": 1}
            for i, (u, n, p, b, pts, t) in enumerate(base)
        ]

    # ── products / orders ────────────────────────────────────────────────
    def products(self, ttl: float = 20.0):
        rows = self.query(
            "SELECT ProductId, ProductName, Category, Price, Stock, IconPath"
            " FROM Products WHERE IsActive = 1 ORDER BY Category, ProductName",
            ttl=ttl, key="products",
        )
        return rows or self.demo_products()

    def demo_products(self):
        items = [
            ("Red Bull 250مل", "مشروبات", 12.0, 24, "🥤"),
            ("قهوة مثلجة", "مشروبات", 15.0, 40, "🧋"),
            ("ماء 600مل", "مشروبات", 2.0, 80, "💧"),
            ("برينجلز كبير", "سناكس", 10.0, 18, "🍟"),
            ("شوكولاتة جالاكسي", "سناكس", 7.0, 35, "🍫"),
            ("ساندويتش دجاج", "وجبات", 22.0, 12, "🥪"),
            ("ساعة لعب إضافية", "خدمات", 25.0, 999, "⏱️"),
            ("باقة 3 ساعات", "خدمات", 60.0, 999, "🎟️"),
        ]
        return [
            {"ProductId": i + 1, "ProductName": name, "Category": cat,
             "Price": price, "Stock": stock, "Icon": icon}
            for i, (name, cat, price, stock, icon) in enumerate(items)
        ]

    def orders_today(self):
        row = self.query(
            "SELECT ISNULL(SUM(FinalAmount), 0) AS total, COUNT(*) AS count"
            " FROM Orders WHERE CAST(CreatedAt AS DATE) = CAST(GETDATE() AS DATE)",
            ttl=15, key="orders_today",
        )
        if row:
            return row
        orders = self.demo_orders()
        return {"total": round(sum(o["FinalAmount"] for o in orders), 2), "count": len(orders)}

    def recent_orders(self, limit: int = 8):
        rows = self.query(
            f"SELECT TOP {int(limit)} ProductName, Quantity, FinalAmount, CreatedAt, Status"
            " FROM Orders ORDER BY OrderId DESC", ttl=10, key="recent_orders",
        )
        return rows or self.demo_orders()

    def demo_orders(self):
        now = datetime.now()
        samples = [("Red Bull 250مل", 2, 24.0, 6), ("ساعة لعب إضافية", 1, 25.0, 14),
                   ("ساندويتش دجاج", 1, 22.0, 27), ("ماء 600مل", 3, 6.0, 41),
                   ("باقة 3 ساعات", 1, 60.0, 58)]
        return [
            {"ProductName": name, "Quantity": qty, "FinalAmount": amount,
             "CreatedAt": now - timedelta(minutes=minutes), "Status": "مكتمل"}
            for name, qty, amount, minutes in samples
        ]

    # ── settings (small JSON blobs) ──────────────────────────────────────
    def setting(self, key: str, default=None):
        rows = self.query(
            "SELECT SettingValue FROM Settings WHERE SettingKey = ?",
            (key,), ttl=30, key=f"setting:{key}",
        )
        if not rows:
            return default
        raw = rows[0].get("SettingValue") or ""
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return raw or default

    def set_setting(self, key: str, value, group: str = "general") -> bool:
        raw = json.dumps(value, ensure_ascii=False)
        sql = (
            "IF EXISTS (SELECT 1 FROM Settings WHERE SettingKey = ?)"
            " UPDATE Settings SET SettingValue = ? WHERE SettingKey = ?"
            " ELSE INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES (?, ?, ?)"
        )
        return self.execute(sql, (key, raw, key, key, raw, group))

    # ── sessions ─────────────────────────────────────────────────────────
    def active_sessions(self, ttl: float = 2.0):
        rows = self.query(
            "SELECT SessionId, HostId, MemberId, GuestName, SessionType, StartTime,"
            " Duration, Cost, Status, HostName, MemberName, HostGroup, BillingProfile,"
            " HourlyRate, PaidMode, MinutesPurchased, AmountCharged"
            " FROM Sessions WHERE Status = N'نشط' ORDER BY StartTime DESC",
            ttl=ttl, key="active_sessions",
        )
        return rows or []

    def recent_sessions(self, limit: int = 40, ttl: float = 6.0):
        rows = self.query(
            f"SELECT TOP {int(limit)} SessionId, HostId, GuestName, MemberName, StartTime,"
            " EndTime, Duration, Cost, Status, HostName, HostGroup, PaidMode"
            " FROM Sessions ORDER BY SessionId DESC",
            ttl=ttl, key="recent_sessions",
        )
        return rows or []

    def shifts(self, ttl: float = 5.0):
        rows = self.query(
            "SELECT TOP 40 ShiftId, StaffName, OpenedAt, ClosedAt, OpeningCash,"
            " ExpectedCash, ClosingCash, Difference, SalesCount, Status, Note"
            " FROM Shifts ORDER BY ShiftId DESC",
            ttl=ttl, key="shifts",
        )
        return rows or self.demo_shifts()

    def demo_shifts(self):
        now = datetime.now()
        return [
            {"ShiftId": 103, "StaffName": "أحمد سامي", "OpenedAt": now.replace(hour=16, minute=0, second=0),
             "ClosedAt": None, "OpeningCash": 300.0, "ExpectedCash": 0.0, "ClosingCash": 0.0,
             "Difference": 0.0, "SalesCount": 0, "Status": "مفتوحة", "Note": ""},
            {"ShiftId": 102, "StaffName": "منى عبد الله",
             "OpenedAt": (now - timedelta(days=1)).replace(hour=8, minute=5, second=0),
             "ClosedAt": (now - timedelta(days=1)).replace(hour=16, minute=2, second=0),
             "OpeningCash": 250.0, "ExpectedCash": 1_180.0, "ClosingCash": 1_200.0,
             "Difference": 20.0, "SalesCount": 34, "Status": "مغلقة", "Note": "إيصال ناقص"},
            {"ShiftId": 101, "StaffName": "أحمد سامي",
             "OpenedAt": (now - timedelta(days=2)).replace(hour=16, minute=0, second=0),
             "ClosedAt": (now - timedelta(days=2)).replace(hour=23, minute=55, second=0),
             "OpeningCash": 300.0, "ExpectedCash": 865.5, "ClosingCash": 850.0,
             "Difference": -15.5, "SalesCount": 21, "Status": "مغلقة", "Note": "عجز بسيط"},
        ]

    def cash_movements(self, shift_id=None, ttl: float = 5.0):
        if shift_id:
            rows = self.query(
                "SELECT TOP 60 MovementId, ShiftId, Kind, Amount, Reason, CreatedBy,"
                " CreatedAt FROM CashMovements WHERE ShiftId = ? ORDER BY MovementId DESC",
                (shift_id,), ttl=ttl, key=f"cash_movements_{shift_id}",
            )
        else:
            rows = self.query(
                "SELECT TOP 60 MovementId, ShiftId, Kind, Amount, Reason, CreatedBy,"
                " CreatedAt FROM CashMovements ORDER BY MovementId DESC",
                ttl=ttl, key="cash_movements",
            )
        return rows or self.demo_cash_movements(shift_id)

    def demo_cash_movements(self, shift_id=None):
        now = datetime.now()
        rows = [
            {"MovementId": 3, "ShiftId": 103, "Kind": "in", "Amount": 120.0,
             "Reason": "إيداع نقدي من لاعب", "CreatedBy": "أحمد سامي",
             "CreatedAt": now - timedelta(minutes=25)},
            {"MovementId": 2, "ShiftId": 103, "Kind": "out", "Amount": 40.0,
             "Reason": "شراء مستلزمات", "CreatedBy": "أحمد سامي",
             "CreatedAt": now - timedelta(minutes=70)},
            {"MovementId": 1, "ShiftId": 102, "Kind": "in", "Amount": 60.0,
             "Reason": "تسوية نهاية اليوم", "CreatedBy": "منى عبد الله",
             "CreatedAt": now - timedelta(days=1)},
        ]
        if shift_id:
            return [row for row in rows if row["ShiftId"] == shift_id]
        return rows

    # ── games ────────────────────────────────────────────────────────────
    def games(self, ttl: float = 20.0):
        rows = self.query(
            "SELECT GameId, GameName, Category, Platform, ExePath, IconPath, TrailerUrl,"
            " Description FROM Games WHERE IsVisible = 1 ORDER BY GameName",
            ttl=ttl, key="games",
        )
        return rows or self.demo_games()

    def demo_games(self):
        samples = [
            ("EA SPORTS FC 25", "ألعاب رياضة", "EA App", "https://www.youtube.com/watch?v=8367UsX3D4U"),
            ("VALORANT", "شوتر", "Riot", "https://www.youtube.com/watch?v=e_E9W2vsRbA"),
            ("Call of Duty: Warzone", "شوتر", "Battle.net", "https://www.youtube.com/watch?v=0E44INyxEVk"),
            ("Grand Theft Auto V", "مغامرات", "Steam", "https://www.youtube.com/watch?v=QkkoHAzjinY"),
            ("League of Legends", "استراتيجية", "Riot", "https://www.youtube.com/watch?v=aR-KAldshAE"),
            ("Counter-Strike 2", "شوتر", "Steam", "https://www.youtube.com/watch?v=c80VVp04Gdc"),
        ]
        return [
            {"GameId": None, "GameName": name, "Category": cat, "Platform": platform,
             "ExePath": "", "IconPath": "", "TrailerUrl": url, "Description": ""}
            for name, cat, platform, url in samples
        ]

    def categories(self):
        rows = self.query("SELECT CategoryName FROM GameCategories WHERE IsActive = 1",
                          ttl=60, key="categories")
        names = [row.get("CategoryName") for row in rows if row.get("CategoryName")]
        return names or ["ألعاب قتال", "ألعاب رياضة", "شوتر", "مغامرات", "استراتيجية"]

    # ── finance ──────────────────────────────────────────────────────────
    def transactions(self, limit: int = 12):
        rows = self.query(
            f"SELECT TOP {int(limit)} t.TransId, t.TransType, t.Amount, t.Description,"
            " t.CreatedAt, m.Username FROM TransactionHistory t"
            " LEFT JOIN Members m ON m.MemberId = t.MemberId"
            " ORDER BY t.TransId DESC", ttl=8, key="transactions",
        )
        return rows or self.demo_transactions()

    def demo_transactions(self):
        now = datetime.now()
        rows = [
            ("إيداع", 150.0, "شحن رصيد", "ahmed99", 12),
            ("سحب", -60.0, "تسوية جلسة", "khalid_x", 38),
            ("إيداع", 320.5, "شحن باقة", "noura.g", 64),
            ("شراء", -22.0, "ساندويتش دجاج", "fahad2", 90),
        ]
        return [
            {"TransType": kind, "Amount": amount, "Description": desc,
             "Username": user, "CreatedAt": now - timedelta(minutes=mins)}
            for kind, amount, desc, user, mins in rows
        ]

    def today_stats(self):
        """Counts used by the overview page."""
        hosts = self.hosts()
        busy = sum(1 for h in hosts if str(h.get("Status")) in ("مشغول", "InUse", "Busy"))
        total = len(hosts)
        members = self.members()
        active = len(members) if not self.live else len([m for m in members if m.get("IsActive")])
        sales = self.orders_today() or {}
        if isinstance(sales, list):
            sales = sales[0] if sales else {}
        revenue = float(sales.get("total") or 0)
        if not self.live:
            revenue = 486.0
        return {
            "hosts_total": total,
            "hosts_busy": busy,
            "hosts_idle": total - busy,
            "members": active,
            "revenue": revenue,
            "orders": int(sales.get("count") or 0),
        }
