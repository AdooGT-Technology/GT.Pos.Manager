# -*- coding: utf-8 -*-
"""Data access used by both the server and the manager.

One short-lived connection per call keeps things simple; the timeout in the
connection string stops a missing SQL Server from freezing the UI for 30s.
"""

from __future__ import annotations

import logging

import pyodbc

from Server.config import DB_NAME, get_connection_string, get_master_connection_string

log = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.conn_str = get_connection_string()

    # ── connections ──────────────────────────────────────────────────────
    def get_connection(self):
        return pyodbc.connect(self.conn_str, autocommit=True)

    def execute_query(self, query, params=None, fetch=True):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if not fetch:
                return True
            if cursor.description is None:
                return []
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as error:  # noqa: BLE001 - logged, callers handle empties
            log.warning("DB error: %s", error)
            return [] if fetch else False
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def execute_non_query(self, query, params=None) -> bool:
        return self.execute_query(query, params, fetch=False)

    # ── setup ────────────────────────────────────────────────────────────
    def ensure_database(self):
        try:
            conn = pyodbc.connect(get_master_connection_string(), autocommit=True)
            cursor = conn.cursor()
            cursor.execute(
                f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name='{DB_NAME}')"
                f" CREATE DATABASE [{DB_NAME}]"
            )
            conn.close()
            return True
        except Exception as error:  # noqa: BLE001
            log.error("DB create error: %s", error)
            return False

    def test_connection(self):
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception:
            return False

    # ── helpers used by the socket server ───────────────────────────────
    def update_host_ping(self, ip: str):
        return self.execute_query(
            "UPDATE Hosts SET Status = CASE WHEN Status = N'مغلق' THEN N'متاح' ELSE Status END"
            " WHERE IPAddress = ?",
            (ip,), fetch=False,
        )

    def authenticate_member(self, username: str, password: str):
        rows = self.execute_query(
            "SELECT MemberId, Username, FullName, Balance, Points, MemberType"
            " FROM Members WHERE LOWER(Username) = LOWER(?) AND PasswordHash = ? AND IsActive = 1",
            (username, password),
        )
        return rows[0] if rows else None

    def get_dashboard_stats(self):
        rows = self.execute_query(
            "SELECT"
            " (SELECT COUNT(*) FROM Hosts WHERE IsActive = 1) AS hosts,"
            " (SELECT COUNT(*) FROM Hosts WHERE Status = N'مشغول') AS busy,"
            " (SELECT COUNT(*) FROM Members WHERE IsActive = 1) AS members,"
            " (SELECT ISNULL(SUM(FinalAmount), 0) FROM Orders"
            "   WHERE CAST(CreatedAt AS DATE) = CAST(GETDATE() AS DATE)) AS revenue"
        )
        return rows[0] if rows else {}

    def log_activity(self, description: str, details: str = "", kind: str = "info"):
        return self.execute_query(
            "INSERT INTO ActivityLog (LogType, UserName, Description, Details)"
            " VALUES (?, ?, ?, ?)",
            (kind, "server", description, details), fetch=False,
        )


Database = DatabaseManager
