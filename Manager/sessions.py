# -*- coding: utf-8 -*-
"""Live session engine.

A session consumes time in the same order Gizmo does:
time offers / fixed time first, then the member's deposit balance.
The engine ticks once per second from the UI; every completed minute is
charged, and the session closes itself when the balance runs out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from Manager.billing import BillingCatalog, format_minutes

ACTIVE = "نشط"
ENDED = "منتهية"

MODE_LABELS = {
    "deposit": "رصيد",
    "fixed": "وقت ثابت",
    "offer": "عرض وقت",
    "guest": "ضيف",
}


def _as_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.now()
    text = str(value).replace("T", " ")[:19]
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return datetime.now()


@dataclass
class LiveSession:
    session_id: int
    host_id: int
    host_name: str
    host_group: str
    member_id: int = None
    member_name: str = "ضيف"
    member_group: str = "زائر"
    mode: str = "deposit"
    started: datetime = field(default_factory=datetime.now)
    ended: datetime = None
    profile: str = ""
    hourly: float = 0.0
    purchased_minutes: int = 0
    used_minutes: int = 0
    charged: float = 0.0
    status: str = ACTIVE
    final_cost: float = 0.0
    opened_by: str = "manager"

    # ── derived values ───────────────────────────────────────────────────
    @property
    def elapsed_minutes(self) -> int:
        if self.ended is not None:
            delta = self.ended - self.started
        else:
            delta = datetime.now() - self.started
        return max(0, int(delta.total_seconds() // 60))

    @property
    def minutes(self) -> int:
        if self.purchased_minutes:
            return self.purchased_minutes
        return self.elapsed_minutes

    @property
    def cost(self) -> float:
        minutes = self.purchased_minutes or self.elapsed_minutes
        return round(minutes / 60.0 * self.hourly, 2)

    @property
    def per_minute(self) -> float:
        return round(self.hourly / 60.0, 4)

    def remaining_minutes(self, balance_minutes: int = 0) -> int:
        total = self.purchased_minutes + balance_minutes
        if total <= 0:
            return 0
        return max(0, total - self.elapsed_minutes)

    def label(self) -> str:
        return MODE_LABELS.get(self.mode, self.mode)

    def usage_plan(self, balance_minutes: int = 0):
        """Split the elapsed time across the three sources, in Gizmo order.

        Bought time (an offer or a fixed block) is consumed first, then the
        deposit balance; anything beyond that is charged as overrun.
        """
        used = self.elapsed_minutes
        left = used
        plan = []
        for name, minutes in ((self.label(), self.purchased_minutes),
                              ("رصيد", balance_minutes)):
            if minutes <= 0:
                continue
            taken = min(minutes, left)
            plan.append((name, taken, minutes))
            left -= taken
        if left > 0:
            plan.append(("تجاوز", left, left))
        return plan


class SessionEngine:
    """Owns live sessions for both the database and the demo fallback."""

    def __init__(self, data):
        self.data = data
        self.catalog = BillingCatalog(data)
        self._demo = []
        self._load_demo()

    # ── demo data ────────────────────────────────────────────────────────
    def _load_demo(self):
        now = datetime.now()
        hosts = self.data.hosts() if hasattr(self.data, "hosts") else []
        members = self.data.members() if hasattr(self.data, "members") else []
        busy = [host for host in hosts if str(host.get("Status")) in ("مشغول", "InUse", "Busy")]
        funded = [m for m in members if float(m.get("Balance") or 0) >= 20] or members
        for index, host in enumerate(busy[:5]):
            member = funded[index % len(funded)] if funded else None
            started = now - timedelta(minutes=25 + index * 17)
            rate = self.catalog.rate_for(
                (member or {}).get("MemberGroup") or "عادي",
                host.get("HostGroup") or "أجهزة PC", started,
            )
            mode = "offer" if index == 1 else ("fixed" if index == 3 else "deposit")
            self._demo.append(LiveSession(
                session_id=1000 + index,
                host_id=host.get("HostId"),
                host_name=str(host.get("HostName")),
                host_group=str(host.get("HostGroup") or "أجهزة PC"),
                member_id=(member or {}).get("MemberId"),
                member_name=str((member or {}).get("FullName") or host.get("CurrentUser") or "ضيف"),
                member_group=str((member or {}).get("MemberGroup") or "عادي"),
                mode=mode,
                started=started,
                profile=rate["profile"],
                hourly=rate["hourly"],
                purchased_minutes=180 if mode == "offer" else (120 if mode == "fixed" else 0),
                charged=0.0,
            ))

    # ── persistence ──────────────────────────────────────────────────────
    def _live(self) -> bool:
        try:
            return bool(self.data.live)
        except Exception:
            return False

    def sessions(self):
        """Active sessions, from the database when live, else the demo list."""
        if not self._live():
            return [s for s in self._demo if s.status == ACTIVE]
        rows = []
        for row in self.data.active_sessions():
            rate = self.catalog.rate_for(
                "عادي", row.get("HostGroup") or "أجهزة PC", _as_datetime(row.get("StartTime"))
            )
            rows.append(LiveSession(
                session_id=int(row.get("SessionId") or 0),
                host_id=int(row.get("HostId") or 0),
                host_name=str(row.get("HostName") or f"PC-{row.get('HostId')}"),
                host_group=str(row.get("HostGroup") or "أجهزة PC"),
                member_id=row.get("MemberId"),
                member_name=str(row.get("MemberName") or row.get("GuestName") or "ضيف"),
                member_group="عادي",
                mode=str(row.get("PaidMode") or "deposit"),
                started=_as_datetime(row.get("StartTime")),
                profile=str(row.get("BillingProfile") or rate["profile"]),
                hourly=float(row.get("HourlyRate") or rate["hourly"]),
                purchased_minutes=int(row.get("MinutesPurchased") or 0),
                charged=float(row.get("AmountCharged") or 0),
            ))
        return rows

    def history(self, limit: int = 30):
        if not self._live():
            ended = [s for s in self._demo if s.status == ENDED]
            return ended[-limit:]
        return self.data.recent_sessions(limit)

    def member_minutes(self, member_id) -> int:
        if not member_id:
            return 0
        for member in self.data.members():
            if int(member.get("MemberId") or 0) == int(member_id):
                return int(member.get("PurchasedMinutes") or 0)
        return 0

    # ── lifecycle ────────────────────────────────────────────────────────
    def start(self, host: dict, member: dict = None, minutes: int = 0,
              mode: str = "deposit", amount: float = 0.0) -> LiveSession:
        group = (member or {}).get("MemberGroup") or "زائر"
        host_group = host.get("HostGroup") or "أجهزة PC"
        rate = self.catalog.rate_for(group, host_group)
        minutes = int(minutes or 0)
        session = LiveSession(
            session_id=(max([s.session_id for s in self._demo], default=1000) + 1),
            host_id=host.get("HostId"),
            host_name=str(host.get("HostName")),
            host_group=str(host_group),
            member_id=(member or {}).get("MemberId"),
            member_name=str((member or {}).get("FullName") or "ضيف"),
            member_group=str(group),
            mode=mode if minutes else ("guest" if not member else "deposit"),
            started=datetime.now(),
            profile=rate["profile"],
            hourly=rate["hourly"],
            purchased_minutes=minutes,
            charged=round(float(amount or 0), 2),
        )
        if not self._live():
            self._demo.append(session)
            self._mark_host(host.get("HostId"), session.member_name, True)
            return session

        self.data.execute(
            "INSERT INTO Sessions (HostId, MemberId, GuestName, SessionType, Status,"
            " HostName, MemberName, HostGroup, BillingProfile, HourlyRate, PaidMode,"
            " MinutesPurchased, AmountCharged) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (session.host_id, session.member_id, session.member_name, "عادي", ACTIVE,
             session.host_name, session.member_name, session.host_group,
             session.profile, session.hourly, session.mode, session.purchased_minutes,
             session.charged),
        )
        self._mark_host(session.host_id, session.member_name, True)
        self.data.invalidate()
        return session

    def extend(self, session: LiveSession, minutes: int, paid: float = 0.0):
        session.purchased_minutes += int(minutes)
        session.charged = round(session.charged + float(paid or 0), 2)
        if self._live():
            self.data.execute(
                "UPDATE Sessions SET MinutesPurchased = ?, AmountCharged = ? WHERE SessionId = ?",
                (session.purchased_minutes, session.charged, session.session_id),
            )
            self.data.invalidate()
        return session

    def stop(self, session: LiveSession, settle: bool = True):
        session.ended = datetime.now()
        session.status = ENDED
        cost = round(minimum_charge(self.catalog, session), 2)
        session.charged = max(session.charged, cost)
        session.final_cost = cost
        if self._live():
            self.data.execute(
                "UPDATE Sessions SET Status = ?, EndTime = GETDATE(), Duration = ?, Cost = ?,"
                " AmountCharged = ? WHERE SessionId = ?",
                (ENDED, session.elapsed_minutes, cost, session.charged, session.session_id),
            )
            if settle and session.member_id:
                self.data.execute(
                    "UPDATE Members SET Balance = Balance - ? WHERE MemberId = ?",
                    (cost, session.member_id),
                )
                self.data.execute(
                    "INSERT INTO TransactionHistory (MemberId, HostId, TransType, Amount,"
                    " Description, CreatedBy) VALUES (?, ?, ?, ?, ?, ?)",
                    (session.member_id, session.host_id, "جلسة", -cost,
                     f"جلسة {session.host_name} — {format_minutes(session.elapsed_minutes)}",
                     session.opened_by),
                )
            self.data.invalidate()
        self._mark_host(session.host_id, "", False)
        return cost

    def tick(self):
        """Charge elapsed minutes and report sessions that need attention."""
        events = []
        for session in self.sessions():
            if session.hourly <= 0:
                continue
            balance_minutes = int(self._member_balance(session.member_id) / session.hourly * 60)
            remaining = session.remaining_minutes(balance_minutes)
            if remaining <= 0:
                events.append(("expired", session, 0))
            elif remaining <= 10:
                events.append(("low", session, remaining))
        return events

    def _member_balance(self, member_id) -> float:
        if not member_id:
            return 0.0
        for member in self.data.members():
            if int(member.get("MemberId") or 0) == int(member_id):
                return float(member.get("Balance") or 0)
        return 0.0

    def _mark_host(self, host_id, user: str, busy: bool):
        if self._live():
            self.data.execute(
                "UPDATE Hosts SET Status = ?, CurrentUser = ? WHERE HostId = ?",
                ("مشغول" if busy else "متاح", user if busy else "", host_id),
            )
            self.data.invalidate()


def minimum_charge(catalog: BillingCatalog, session: LiveSession) -> float:
    """Apply the profile's minimum session length."""
    minutes = max(session.elapsed_minutes, 1)
    profile = catalog.profile(session.profile) or {}
    minimum = int(float(profile.get("minimum") or 0))
    if minimum:
        minutes = max(minutes, minimum)
    return round(minutes / 60.0 * session.hourly, 2)
