# -*- coding: utf-8 -*-
"""Billing engine.

Mirrors the way Gizmo prices a session:

* every member belongs to a **user group** with a default billing profile,
* every host belongs to a **host group** which may override that profile,
* a profile has an hourly rate plus optional custom rates per time window,
* time can be sold as **time offers**, **fixed time** or left as a **deposit**.
"""

from __future__ import annotations

from datetime import datetime, time as clock_time

DEFAULT_PROFILES = [
    {"name": "التسعير الأساسي", "hourly": 15, "minimum": 30, "round": 15, "active": True,
     "custom": "18:00-23:00=20;23:00-06:00=12"},
    {"name": "تسعير VIP", "hourly": 25, "minimum": 60, "round": 15, "active": True,
     "custom": "18:00-23:00=30"},
    {"name": "تسعير الكونسول", "hourly": 20, "minimum": 30, "round": 15, "active": True,
     "custom": ""},
    {"name": "تسعير البطولات", "hourly": 35, "minimum": 60, "round": 30, "active": True,
     "custom": "18:00-23:00=40"},
]

DEFAULT_USER_GROUPS = [
    {"name": "زائر", "kind": "guest", "profile": "التسعير الأساسي", "discount": 0, "points": 1, "active": True},
    {"name": "عادي", "kind": "member", "profile": "التسعير الأساسي", "discount": 0, "points": 1, "active": True},
    {"name": "VIP", "kind": "member", "profile": "تسعير VIP", "discount": 15, "points": 2, "active": True},
    {"name": "eSports", "kind": "member", "profile": "تسعير البطولات", "discount": 10, "points": 2, "active": True},
]

DEFAULT_HOST_GROUPS = [
    {"name": "أجهزة PC", "profile": "", "note": "السعر الافتراضي لمجموعة العضو"},
    {"name": "غرف VIP", "profile": "تسعير VIP", "note": "سعر أعلى للأجهزة المميزة"},
    {"name": "بلايستيشن", "profile": "تسعير الكونسول", "note": "أجهزة كونسول"},
]

DEFAULT_OFFERS = [
    {"name": "عرض الساعة الذهبية", "minutes": 60, "price": 12, "from": "14:00", "to": "17:00", "active": True},
    {"name": "باقة 3 ساعات", "minutes": 180, "price": 35, "from": "", "to": "", "active": True},
    {"name": "ليلة كاملة", "minutes": 300, "price": 50, "from": "23:00", "to": "05:00", "active": True},
    {"name": "عرض نهاية الأسبوع", "minutes": 240, "price": 45, "from": "", "to": "", "active": False},
]


def format_minutes(minutes) -> str:
    try:
        total = int(round(float(minutes)))
    except (TypeError, ValueError):
        return "—"
    if total <= 0:
        return "0 د"
    hours, rest = divmod(total, 60)
    if hours and rest:
        return f"{hours} س {rest} د"
    if hours:
        return f"{hours} س"
    return f"{rest} د"


def _parse_clock(text: str, fallback: clock_time) -> clock_time:
    try:
        hours, minutes = str(text).strip().split(":")
        return clock_time(int(hours) % 24, int(minutes) % 60)
    except (ValueError, TypeError):
        return fallback


def _in_window(start: clock_time, end: clock_time, moment: clock_time) -> bool:
    if start <= end:
        return start <= moment < end
    return moment >= start or moment < end


class BillingCatalog:
    """Reads the four catalogues and resolves the rate for a session."""

    def __init__(self, data):
        self.data = data

    # ── raw rows ─────────────────────────────────────────────────────────
    def _rows(self, key: str, fallback):
        store = getattr(self.data, "settings", None)
        if store is not None:
            try:
                payload = store.section(key)
                rows = payload.get("rows") if isinstance(payload, dict) else None
                if rows:
                    return rows
            except Exception:
                pass
        return list(fallback)

    def profiles(self):
        return self._rows("billing.profiles", DEFAULT_PROFILES)

    def user_groups(self):
        return self._rows("billing.usergroups", DEFAULT_USER_GROUPS)

    def host_groups(self):
        return self._rows("billing.hostgroups", DEFAULT_HOST_GROUPS)

    def offers(self):
        return self._rows("billing.offers", DEFAULT_OFFERS)

    # ── lookups ──────────────────────────────────────────────────────────
    def profile(self, name: str):
        for row in self.profiles():
            if str(row.get("name")) == str(name):
                return row
        return None

    def user_group(self, name: str):
        for row in self.user_groups():
            if str(row.get("name")) == str(name):
                return row
        return None

    def host_group(self, name: str):
        for row in self.host_groups():
            if str(row.get("name")) == str(name):
                return row
        return None

    def profile_for(self, member_group: str, host_group: str) -> dict:
        host = self.host_group(host_group) or {}
        override = str(host.get("profile") or "").strip()
        if override:
            profile = self.profile(override)
            if profile:
                return profile
        group = self.user_group(member_group) or {}
        profile = self.profile(str(group.get("profile") or "التسعير الأساسي"))
        if profile:
            return profile
        return (self.profiles() or DEFAULT_PROFILES)[0]

    def rate_for(self, member_group: str, host_group: str, at: datetime = None) -> dict:
        """Resolved rate: profile, hourly price and the applied window."""
        profile = self.profile_for(member_group, host_group)
        at = at or datetime.now()
        hourly = float(profile.get("hourly") or 0)
        window = ""
        for chunk in str(profile.get("custom") or "").split(";"):
            if "=" not in chunk or "-" not in chunk.split("=")[0]:
                continue
            span, price = chunk.split("=", 1)
            start_text, end_text = span.split("-", 1)
            start = _parse_clock(start_text, clock_time(0, 0))
            end = _parse_clock(end_text, clock_time(23, 59))
            if _in_window(start, end, at.time()):
                try:
                    hourly = float(price)
                except ValueError:
                    continue
                window = f"{start_text}-{end_text}"
                break
        group = self.user_group(member_group) or {}
        discount = float(group.get("discount") or 0)
        if discount:
            hourly = round(hourly * (1 - discount / 100.0), 2)
        return {
            "profile": str(profile.get("name") or "التسعير الأساسي"),
            "hourly": hourly,
            "base_hourly": float(profile.get("hourly") or 0),
            "minimum": int(float(profile.get("minimum") or 0)),
            "round": max(1, int(float(profile.get("round") or 1))),
            "window": window,
            "discount": discount,
        }

    # ── money ────────────────────────────────────────────────────────────
    def cost(self, minutes, hourly) -> float:
        try:
            return round(float(minutes) / 60.0 * float(hourly), 2)
        except (TypeError, ValueError):
            return 0.0

    def minutes_for_money(self, amount, rate: dict) -> int:
        hourly = float(rate.get("hourly") or 0)
        if hourly <= 0:
            return 0
        minutes = int(float(amount) / hourly * 60)
        step = int(rate.get("round") or 15)
        minutes = (minutes // step) * step
        return max(minutes, 0)

    def active_offers(self, at: datetime = None):
        at = at or datetime.now()
        rows = []
        for offer in self.offers():
            if not offer.get("active", True):
                continue
            start = str(offer.get("from") or "").strip()
            end = str(offer.get("to") or "").strip()
            if start and end:
                if not _in_window(_parse_clock(start, clock_time(0, 0)),
                                  _parse_clock(end, clock_time(23, 59)), at.time()):
                    continue
            rows.append(offer)
        return rows

    def summary(self) -> dict:
        return {
            "profiles": len(self.profiles()),
            "user_groups": len(self.user_groups()),
            "host_groups": len(self.host_groups()),
            "offers": len([o for o in self.offers() if o.get("active", True)]),
        }
