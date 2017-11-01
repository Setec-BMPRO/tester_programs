#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panasonic eUniStone PAN1322 Bluetooth Radio interface.

A Bluetooth v2.1 development board with a USB serial interface.

"""

import logging
import time
import re
import json
from ._base import BluetoothError, BluetoothMAC


class BtRadio():

    """BT Radio interface functions."""

    # Command to escape from streaming data mode
    cmd_escape = '^^^'
    # Some magic numbers for PIN generation from a serial number
    hash_start = 56210
    hash_mult = 29

    def __init__(self, port):
        """Create.

        @param port Serial port

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.port = port
        self._mac = None         # MAC address
        self._pin = None         # PIN
        self._datamode = False   # True for data mode

    def open(self):
        """Open communications with BT Radio.

           Software reset.
           Enable security.

        """
        self._logger.debug('Open')
        self.port.rtscts = True
        self.port.open()
        time.sleep(1)
        self.port.flushInput()
        for _ in range(0, 5):
            try:
                self._cmdresp('AT+JRES')    # reset
                self._cmdresp('AT+JSEC=4,1,04,1111,2,1')    # security mode
                return
            except BluetoothError:
                time.sleep(2)
                continue
        raise BluetoothError('Unable to reset radio')

    def close(self):
        """Close serial communications with BT Radio."""
        self._logger.debug('Close')
        self.port.rtscts = False   # so close() does not hang
        self.port.close()

    def _log(self, message):
        """Helper method to Log messages."""
        self._logger.debug(message)

    def _readline(self):
        """Read a line from the port and decode to a string."""
        line = self.port.readline().decode(errors='ignore')
        return line.replace('\r\n', '')

    def _write(self, data):
        """Encode data and write to the port."""
        self.port.write(data.encode())

    def _cmdresp(self, cmd):
        """Send a command to the modem and process the response.

        @raises BluetoothError upon error.

        """
        self.port.flushInput()
        if cmd == self.cmd_escape:
            time.sleep(1)       # need long guard time before first letter
            for _ in range(0, 3):
                time.sleep(0.2) # need short guard time between letters
                self._write('^')
        else:
            self._log('--> {0!r}'.format(cmd))
            self._write(cmd + '\r\n')
        line = self._readline()
        self._log('<-- {0!r}'.format(line))
        # Request for firmware version returns only simple integer
        if cmd == 'AT+JRRI':
            if not re.search('^[0-9]+$', line):
                raise BluetoothError('Unknown firmware version response')
        else:
            # Other requests return OK,
            #  or ROK if AT+JRES and after hardware reset
            if not re.search('^R?OK$', line):
                raise BluetoothError('OK response not received')

    @classmethod
    def _pin_calculate(cls, sernum):
        """Generate a PIN from a serial number.

        @return 4 character PIN number string

        """
        if len(sernum) != 11:
            raise BluetoothError('Serial number must be 11 characters')
        pin = cls.hash_start
        for char in sernum:
            pin = ((pin * cls.hash_mult) & 0xFFFF) ^ ord(char)
        return '{:04}'.format(pin % 10000)

    def scan(self, sernum):
        """Scan for bluetooth device with 'sernum' name.

        @returns True if a match is found, else returns False

        """
        self._log('Scanning for serial number {0}'.format(sernum))
        max_try = 5
        for retry in range(0, max_try):
            try:
                self._cmdresp('AT+JDDS=0')  # start device scan
                break
            except BluetoothError:
                continue
        if retry == max_try - 1:
            raise BluetoothError('Cannot start device scan')
        # Read responses until completed.
        for _ in range(0, 20):
            line = self._readline()
            self._log('<--- {0!r}'.format(line))
            if len(line) == 0:
                continue
            if line == '+RDDSCNF=0':   # no more responses
                break
            match = re.search(
                '^\+RDDSRES=({0}),BCheck ([^,]*),.*'.format(
                    BluetoothMAC.regex),
                line)
            if match:
                data = match.groups()
                if len(data) >= 2:
                    if sernum == data[1]:
                        self._log('SN match found:{0}'.format(data[1]))
                        self._mac = data[0]
                        self._pin = self._pin_calculate(data[1])
        return self._mac is not None

    def pair(self):
        """Pair with the device previously found by a scan.

        @raises BluetoothError upon failure to pair.

        """
        self._log('Pairing with mac {0}'.format(self._mac))
        self._cmdresp('AT+JCCR=' + self._mac + ',01')
        for _ in range(0, 10):
            line = self._readline()
            self._log('<--- {!r}'.format(line))
            if len(line) == 0:
                continue
            # Device we are pairing to has asked for a pin code
            if line[:6] == '+RPCI=':
                self._log('Sending pin code: {0}'.format(self._pin))
                self._cmdresp('AT+JPCR=04,' + self._pin)
                continue
            # Device we are pairing to has asked to verify 6 digit id
            if line[:6] == '+RUCE=':
                self._log('Sending confirmation')
                self._cmdresp('AT+JUCR=1')
                continue
            # Example of good pairing response: '+RCCRCNF=500,0000,0'
            # The first 500 is MTU and is 000 on error.
            # The ',0' on the end means good status and ',1' would be an error.
            if line[:9] == '+RCCRCNF=':
                match = re.search(
                    '^\+RCCRCNF=([1-9][0-9]{2}),([0-9]{4}),([0-9])$', line)
                if not match:
                    continue
                data = match.groups()
                if len(data) < 3:
                    continue
                mtu = int(data[0])
                if mtu == 500:
                    self._log('Now Paired, MTU {0} bytes.'.format(mtu))
                    return
                self._log('Pairing failed.')
                continue
        raise BluetoothError('Unable to pair with device')

    def unpair(self):
        """Unpair with bluetooth device.

        @return True for ok, else False.

        """
        self._log('Unpairing')
        self._cmdresp('AT+JSDR')
        for _ in range(0, 10):      # about 20s due to 2s serial rx timeout
            time.sleep(2)
            line = self._readline()
            if len(line) == 0:
                continue
            self._log('<--- {0!r}'.format(line))
            if line == '+RDII':     # good unpairing response
                self._log('Now Un-Paired.')
                return
        raise BluetoothError('Unpairing timed out')

    def data_mode_enter(self):
        """Enter streaming data mode.

        @return True upon success

        """
        self._log('Entering streaming mode')
        if not self._datamode:
            self._cmdresp('AT+JSCR')
            self._datamode = True

    def data_mode_escape(self):
        """Escape from streaming data mode back to command mode.

        @return True upon success

        """
        self._log('Leaving streaming mode')
        if self._datamode:
            self._cmdresp(self.cmd_escape)
            self._datamode = False

    def jsonrpc(self, method, params=None):
        """Make a JSON-RPC call (when in streaming data mode).

        @param method Method name to call.
        @param params Dictionary of parameters.
        @return Result The 'result' element from the response.

        """
        if not self._datamode:
            raise BluetoothError('JSON-RPC requires streaming data mode')
        if params is None:
            params = {}
        request = {
            'jsonrpc': '2.0', 'id': 8256,
            'method': method, 'params': params}
        cmd = json.dumps(request)
        self._log('JSONRPC request: {0!r}'.format(cmd))
        self.port.flushInput()
        self._write(cmd + '\r')
        response = self._readline()
        self._log('<--- {0!r}'.format(response))
        return json.loads(response)['result']
