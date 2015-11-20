#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MicroChip RN4020 driver.

A Bluetooth 4.1 Low Energy (BLE) module.
The RN4020 module is connected to a FTDI USB Serial interface.

"""

import logging


class BleError(Exception):

    """BLE communications error."""


class BleRadio():

    """Bluetooth Low Energy (BLE) Radio interface functions."""

    def __init__(self, port):
        """Create."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._port = port

    def open(self):
        """Open BLE Radio."""
        self._logger.debug('Open')
        self._port.open()

    def close(self):
        """Close BLE Radio."""
        self._logger.debug('Close')
        self._port.close()

    def _log(self, message):
        """Helper method to Log messages."""
        self._logger.debug(message)

    def _readline(self):
        """Read a line from the port and decode to a string."""
        line = self._port.readline().decode(errors='ignore')
        return line.replace('\r\n', '')

    def _write(self, data):
        """Encode data and write to the port."""
        self._port.write(data.encode())
