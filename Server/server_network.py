# -*- coding: utf-8 -*-
"""Compatibility wrapper.

The socket server lives in :mod:`Server.main`; older entry points imported
``NetworkServer`` from here, so this module keeps that name working.
"""

from Server.main import POSServer

NetworkServer = POSServer

__all__ = ["NetworkServer", "POSServer"]
