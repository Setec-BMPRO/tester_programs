#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MicroChip RN4020 driver.

A Bluetooth 4.1 Low Energy (BLE) module.
The RN4020 module is connected to a FTDI USB Serial interface.

Before use, the module must be configured for use by this module.
The RN4020 module must have Firmware version > 1.20 to be used by this module.
This procedure assumes a module set to the factory defaults.
    Connect to the module at 115200Bd, no hardware flow control.
    '+'             to turn echo ON
    'SF,2'          for a full factory defaults reset
    'R,1'           to restart the module
    '+'             again to turn echo ON
    'SN,ATE_Tester' to set the module's Bluetooth name
    'SR,42100000'   to configure:
        40000000        for Real-Time reading
        02000000        for hardware Flow Control ON
        00100000        to not save bonding information
    'R,1'           to restart the module
    Now, turn on hardware flow control on the port
The module will now remember these settings in NV Memory.

"""

import logging


class BleRadio():

    """Bluetooth Low Energy (BLE) Radio interface functions."""

    # Module command strings
    cmd_ver = 'V'               # Version query
    cmd_scan_start = 'F'        # Start device scan
    cmd_scan_stop = 'X'         # Stop device scan
    # Module response strings
    response_ok = 'AOK'         # 'OK' module response
    response_ver = 'MCHP BTLE'  # Reply is like: MCHP BTLE v1.23.5 8/7/2015
    # Mapping of commands to expected responses
    expect = {
        cmd_ver: response_ver,
        cmd_scan_start: response_ok,
        cmd_scan_stop: response_ok,
        }

    def __init__(self, port):
        """Create instance and setup logging."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.port = port

    def open(self):
        """Open BLE Radio."""
        self._logger.debug('Open')
        self.port.open()
        # Remove 'CMD' response and other rubbish characters at power up.
        try:
            self._cmdresp('')
        except BleError as err:
            self._log('Received: {0}'.format(err))
        self._cmdresp(self.cmd_ver)

    def close(self):
        """Close BLE Radio."""
        self._logger.debug('Close')
        self.port.close()

    def puts(self,
             string_data, preflush=0, postflush=0, priority=False,
             addprompt=True):
        """Push string data into the buffer if simulating."""
        if self.port.simulation:
            if addprompt:
                string_data = string_data + '\r\n'
            self.port.puts(string_data, preflush, postflush, priority)

    def scan(self, btmac):
        """Scan for bluetooth device with 'btmac' MAC address.

        @param btmac Bluetooth MAC address to find
        @returns True if found, else False

        """
        self._log('Scanning for MAC {0}'.format(btmac))
        self._cmdresp(self.cmd_scan_start)
        found = False
        for retry in range(0, 10):
            try:
                # Scan responses look like this:
                #   001EC025B69B,0,,534554454320434E3130310000000000,-53
                line = self._readline()
                self._log('<--- {0!r}'.format(line))
            except BleError:
                continue
            data = line.split(sep=',')  # CSV formatted response
            if data[0] == btmac:
                found = True
                break
        self._cmdresp(self.cmd_scan_stop)
        return found

    def _log(self, message):
        """Helper method to Log messages."""
        self._logger.debug(message)

    def _cmdresp(self, cmd):
        """Send a command to the module and process the response.

        @param cmd Command to send
        @return Response from the command
        @raises BleError upon error.

        """
        self.port.flushInput()
        self._log('--> {0!r}'.format(cmd))
        self.port.write(cmd.encode())
        self.port.write(b'\r')
        reply = self._readline()
        self._log('<-- {0!r}'.format(reply))
        try:    # Lookup any expected response
            expect = self.expect[cmd]
        except KeyError:
            expect = None
        if expect:
            if reply[:len(expect)] != expect:
                raise BleError('Expected {0}, got {1}'.format(expect, reply))
        return reply

    def _readline(self):
        """Read a line from the port and decode to a string.

        @return Response from the module

        """
        line = self.port.readline().decode(errors='ignore')
        if len(line) == 0:
            raise BleError('No response')
        return line.replace('\r\n', '')


class BleError(Exception):

    """BLE communications error."""
