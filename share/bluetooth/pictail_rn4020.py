#!/usr/bin/env python3
"""MicroChip RN4020 PICTAIL driver.

A Bluetooth 4.1 Low Energy development board with a USB serial interface.

"""

import time
import logging

from .sim_serial import SimSerial


class BleError(Exception):

    """BLE communications error."""


class BleRadio():

    """Bluetooth Low Energy (BLE) Radio interface functions."""

    def __init__(self, port):
        """Create."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._port = port
        self._serport = None

    def open(self):
        """Open serial communications with BLE Radio."""
        self._logger.debug('Open')
        self._serport = SimSerial(
            port=self._port, baudrate=115200, timeout=2, rtscts=True)
        time.sleep(1)
        self._serport.flushInput()

    def close(self):
        """Close serial communications with BLE Radio."""
        self._logger.debug('Close')
        self._serport.setRtsCts(False)   # so close() does not hang
        self._serport.close()
        self._serport = None

    def _log(self, message):
        """Helper method to Log messages."""
        self._logger.debug(message)

    def _readline(self):
        """Read a line from the port and decode to a string."""
        line = self._serport.readline().decode(errors='ignore')
        return line.replace('\r\n', '')

    def _write(self, data):
        """Encode data and write to the port."""
        self._serport.write(data.encode())
