#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd.
"""Arduino programmer console driver.

On Linux, something (the ModemManager?) opens the serial port
for a while after it appears.
Wait for it to release the port when open() is called.

"""

import time

from . import protocol


class Arduino(protocol.Base):

    """Communications to Arduino programmer console."""

    def open(self):
        """Open port, with auto re-try."""
        retry_max = 20
        for retry in range(retry_max + 1):
            try:
                super().open()
                break
# TODO: Put the actual exception type here (device busy error)
            except Exception:
                if retry == retry_max:
                    raise
                time.sleep(1)
        # Let the Arduino start after the 'port open reset'
        time.sleep(2)
