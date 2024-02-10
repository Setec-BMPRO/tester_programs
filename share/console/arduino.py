#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd.
"""Arduino programmer console driver.

On xubuntu ModemManager opens the serial port for a while after it appears.
Wait for it to release the port when open() is called.

"""

import logging
import time

import serial

from . import protocol


class Arduino(protocol.Base):

    """Communications to Arduino programmer console."""

    def open(self):
        """Open port, with auto re-try."""
        retry_max = 20
        logger = logging.getLogger(".".join((__name__, self.__class__.__name__)))
        for retry in range(retry_max + 1):
            try:
                super().open()
                break
            except serial.serialutil.SerialException:
                logger.debug("Arduino open failed")
                if retry == retry_max:
                    logger.error("Arduino open timeout")
                    raise
                time.sleep(1)
        # Let the Arduino start after the 'port open reset'
        time.sleep(2)
