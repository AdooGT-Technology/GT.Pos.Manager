# -*- coding: utf-8 -*-
"""Read/write access to the settings catalogue.

Each section is one JSON blob in the Settings table (``settings.<id>``), merged
over the defaults from ``settings_schema``. When the database is unreachable the
values stay in memory so the panel keeps working in demo mode.
"""

from __future__ import annotations

from Manager.settings_schema import find, sections


class SettingsStore:
    def __init__(self, data):
        self.data = data
        self._memory = {}
        self._cache = {}

    # ── section level ─────────────────────────────────────────────────────
    def section(self, section_key: str) -> dict:
        _group, spec = find(section_key)
        defaults = dict((spec or {}).get("defaults") or {})
        stored = self._read(section_key)
        if isinstance(stored, dict):
            for key, value in stored.items():
                if isinstance(value, dict) and isinstance(defaults.get(key), dict):
                    merged = dict(defaults[key])
                    merged.update(value)
                    defaults[key] = merged
                else:
                    defaults[key] = value
        return defaults

    def save_section(self, section_key: str, values: dict) -> bool:
        payload = dict(values)
        self._memory[section_key] = payload
        self._cache.pop(section_key, None)
        try:
            self.data.invalidate()
        except Exception:
            pass
        if not self.data.live:
            return False
        return bool(self.data.set_setting(f"settings.{section_key}", payload, "settings"))

    def _read(self, section_key: str):
        if section_key in self._memory:
            return self._memory[section_key]
        cached = self._cache.get(section_key)
        if cached is not None:
            return cached
        try:
            value = self.data.setting(f"settings.{section_key}", {})
        except Exception:
            value = {}
        self._cache[section_key] = value if isinstance(value, dict) else {}
        return self._cache[section_key]

    def invalidate(self):
        self._memory.clear()
        self._cache.clear()

    # ── cross-section getters used by the other pages ────────────────────
    def value(self, path: str, default=None):
        parts = path.split(".")
        if len(parts) != 2:
            return default
        section_key, key = parts
        return self.section(section_key).get(key, default)

    def currency(self) -> str:
        finance = self.section("currencies")
        code = str(finance.get("default") or "SAR")
        for row in finance.get("rows") or []:
            if str(row.get("code")) == code:
                return str(row.get("symbol") or code)
        return "ر.س"

    def money(self, amount, digits: int = 2) -> str:
        try:
            number = float(amount)
        except (TypeError, ValueError):
            number = 0.0
        return f"{number:,.{digits}f} {self.currency()}"

    def tax(self) -> tuple[float, bool, str]:
        """(rate as fraction, inclusive, label)."""
        tax = self.section("tax")
        try:
            rate = float(tax.get("rate") or 0) / 100.0
        except (TypeError, ValueError):
            rate = 0.0
        if not tax.get("enabled", True):
            rate = 0.0
        return rate, bool(tax.get("inclusive")), str(tax.get("label") or "الضريبة")

    def start_page(self) -> str:
        return str(self.section("dashboard").get("start_page") or "overview")


def section_titles():
    """[(group_title, [(section_key, section_title), ...]), ...] for the tree."""
    tree = []
    for group, section in sections():
        if tree and tree[-1][0] == group["title"]:
            tree[-1][1].append((section["key"], section["title"]))
        else:
            tree.append((group["title"], [(section["key"], section["title"])]))
    return tree
