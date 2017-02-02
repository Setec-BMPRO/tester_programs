#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MicroChip RN4020 driver.

A Bluetooth 4.1 Low Energy (BLE) module.
The RN4020 module is connected to a FTDI USB Serial interface.

Before use, the module must be configured for use by this module.
The RN4020 module must have Firmware version > 1.20 to be used by this module.
This procedure assumes a module set to the factory defaults.
    Connect to the module @ 115200Bd, no HW flow control
    '+' to turn echo ON
    'SF,2' for a full factory defaults reset
    'R,1' to restart the module
    '+' again to turn echo ON
    'SN,ATE_Tester' to set the module's Bluetooth name
    'SR,42100000' to configure:
            40000000 for Real-Time reading
            02000000 for hardware Flow Control ON
            00100000 to not save bonding information
    'R,1' to restart the module
    Now, turn on hardware flow control on the port
The module will now remember these settings in NV Memory.

"""

import logging


# Module command strings
_CMD_VER = 'V'               # Version query
_CMD_SCAN_START = 'F'       # Start device scan
_CMD_SCAN_STOP = 'X'        # Stop device scan

# Module response strings
_RESPONSE_OK = 'AOK'        # 'OK' module response
_RESPONSE_VER = 'MCHP BTLE' # Reply is like: MCHP BTLE v1.23.5 8/7/2015

# Mapping of commands to expected responses
_EXPECT = {
    _CMD_VER: _RESPONSE_VER,
    _CMD_SCAN_START: _RESPONSE_OK,
    _CMD_SCAN_STOP: _RESPONSE_OK,
    }


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
        # Remove 'CMD' response and other rubbish characters at power up.
        try:
            self._cmdresp('')
        except BleError as err:
            self._log('Received: {}'.format(err))
        self._cmdresp(_CMD_VER)

    def close(self):
        """Close BLE Radio."""
        self._logger.debug('Close')
        self._port.close()

    def puts(self,
             string_data, preflush=0, postflush=0, priority=False,
             addcrlf=True):
        """Push string data into the buffer if simulating."""
        if self._port.simulation:
            if addcrlf:
                string_data = string_data + '\r\n'
            self._port.puts(string_data, preflush, postflush, priority)

    def scan(self, btmac):
        """Scan for bluetooth device with 'btmac' MAC address.

        @param btmac Bluetooth MAC address to find
        @returns True if found, else False

        """
        self._log('Scanning for MAC {}'.format(btmac))
        self._cmdresp(_CMD_SCAN_START)  # Start scan
        #   F
        #   AOK
        #   001EC025B69B,0,,534554454320434E3130310000000000,-53
        # Read responses until completed.
        found = False
        for retry in range(0, 10):
            try:
                line = self._readline()
                self._log('<--- {!r}'.format(line))
            except BleError:
                continue
            data = line.split(sep=',')  # CSV formatted response
            if data[0] == btmac:
                found = True
                break
        self._cmdresp(_CMD_SCAN_STOP)  # Stop scanning
        return found

    def _log(self, message):
        """Helper method to Log messages."""
        self._logger.debug(message)

    def _cmdresp(self, cmd):
        """Send a command to the module and process the response.

        @param cmd Command to send
        @raises BleError upon error.

        """
        self._port.flushInput()
        self._log('--> {!r}'.format(cmd))
        self._write(cmd + '\r')
        reply = self._readline()
        self._log('<-- {!r}'.format(reply))
        try:    # Lookup any expected reponse
            expect = _EXPECT[cmd]
        except KeyError:
            expect = None
        if expect:
            if reply[:len(expect)] != expect:
                raise BleError('Expected {}, got {}'.format(expect, reply))
        return reply

    def _readline(self):
        """Read a line from the port and decode to a string."""
        line = self._port.readline().decode(errors='ignore')
        if len(line) == 0:
            raise BleError('No response')
        else:
            return line.replace('\r\n', '')

    def _write(self, data):
        """Encode data and write to the port."""
        self._port.write(data.encode())
