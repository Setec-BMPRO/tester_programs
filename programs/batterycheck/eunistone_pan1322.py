#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2014 SETEC Pty Ltd.
"""Panasonic eUniStone PAN1322 Bluetooth Radio interface.

A Bluetooth v2.1 development board with a USB serial interface.

"""

import json
import logging
import re
import time


class BtRadioError(Exception):

    """Bluetooth error."""


class MAC():

    """Bluetooth MAC address."""

    # Regular expression for a MAC address, with optional ':' characters
    regex = '(?:[0-9A-F]{2}:?){5}[0-9A-F]{2}'
    # Regular expression for a string with only a MAC address
    line_regex = '^{0}$'.format(regex)

    def __init__(self, mac):
        """Create a MAC instance.

        @param mac MAC as a string

        """
        if not re.match(self.line_regex, mac):
            raise BtRadioError('Invalid MAC string')
        self._mac = bytes.fromhex(mac.replace(':', ''))

    def __str__(self):
        """MAC address as a string.

        @return MAC address as 12 uppercase hex digits

        """
        return self.dumps()

    def dumps(self, separator='', lowercase=False):
        """Dump the MAC as a string.

        @param separator String to separate the bytes.
        @param lowercase Convert to lowercase.
        @return MAC as a string.

        """
        data = []
        for abyte in self._mac:
            data.append('{0:02X}'.format(abyte))
        data_str = separator.join(data)
        if lowercase:
            data_str = data_str.lower()
        return data_str


class BtRadio():

    """BT Radio interface functions."""

    # Command to escape from streaming data mode
    cmd_escape = '^^^'
    # Some magic numbers for PIN generation from a serial number
    hash_start = 56210
    hash_mult = 29
    # Retry counters
    reset_retries = 5
    scan_retries = 5
    pair_retries = 4
    unpair_retries = 10

    def __init__(self, port):
        """Create.

        @param port Serial port

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.port = port
        self._datamode = False   # True for data mode

    def open(self):
        """Open communications with BT Radio."""
        self._logger.debug('Open')
        self.port.rtscts = True
        self.port.open()
        time.sleep(1)
        self.reset()

    def close(self):
        """Close communications with BT Radio."""
        self._logger.debug('Close')
        self.port.rtscts = False   # so close() does not hang
        self.port.close()

    def reset(self):
        """Reset the module."""
        self._logger.debug('Reset')
        self.port.flushInput()
        for _ in range(self.reset_retries):
            try:
                self._cmdresp('AT+JRES')                    # Reset
                self._cmdresp('AT+JSEC=4,1,04,1111,2,1')    # Security mode
                return
            except BtRadioError:
                time.sleep(2)
        raise BtRadioError('Unable to reset radio')

    def _log(self, message):
        """Helper method to Log messages."""
        self._logger.debug(message)

    def _readline(self):
        """Read a line from the port and decode to a string."""
        line = self.port.readline().decode(errors='ignore').replace('\r\n', '')
        self._log('<--- {0!r}'.format(line))
        return line

    def _write(self, data):
        """Encode data and write to the port."""
        self.port.write(data.encode())

    def _cmdresp(self, cmd):
        """Send a command to the modem and process the response.

        @raises BtRadioError upon error.

        """
        self.port.flushInput()
        if cmd == self.cmd_escape:
            time.sleep(1)       # need long guard time before first letter
            for char in cmd:
                time.sleep(0.2) # need short guard time between letters
                self._write(char)
        else:
            self._log('--> {0!r}'.format(cmd))
            self._write(cmd + '\r\n')
        line = self._readline()
        # Request for firmware version returns only simple integer
        if cmd == 'AT+JRRI':
            if not re.search('^[0-9]+$', line):
                raise BtRadioError('Unknown firmware version response')
        else:
            # Other requests return OK,
            #  or ROK if AT+JRES and after hardware reset
            if not re.search('^R?OK$', line):
                raise BtRadioError('OK response not received')

    @classmethod
    def _pin_calculate(cls, sernum):
        """Generate a PIN from a serial number.

        @return 4 character PIN number string

        """
        if len(sernum) != 11:
            raise BtRadioError('Serial number must be 11 characters')
        pin = cls.hash_start
        for char in sernum:
            pin = ((pin * cls.hash_mult) & 0xFFFF) ^ ord(char)
        return '{0:04}'.format(pin % 10000)

    def scan(self, sernum):
        """Scan for Bluetooth device with 'sernum' name.

        @returns Tuple (MAC address, or None, PIN or None)

        """
        self._log('Scanning for serial number {0}'.format(sernum))
        regex = re.compile(
            r'^\+RDDSRES=({0}),BCheck {1},.*'.format(MAC.regex, sernum))
        for retry in range(self.scan_retries):
            try:
                self._cmdresp('AT+JDDS=0')  # start device scan
                break
            except BtRadioError:
                continue
        if retry == self.scan_retries - 1:
            raise BtRadioError('Cannot start device scan')
        # Read responses until completed.
        mac = None
        pin = self._pin_calculate(sernum)
        for _ in range(20):
            line = self._readline()
            if line == '':
                continue
            if line == '+RDDSCNF=0':   # no more responses
                break
            match = regex.match(line)
            if match:
                data = match.groups()
                mac = MAC(data[0])
                self._log('Found: MAC {0}, PIN {1}'.format(mac, pin))
        return mac, pin

    def pair(self, mac, pin):
        """Pair with a device.

        @param mac MAC address to pair to.
        @param pin PIN.
        @raises BtRadioError upon failure to pair.

        """
        self._log('Pair with MAC {0} using PIN {1}'.format(mac, pin))
        for retry in range(self.pair_retries):
            if retry > 0:
                self._log('Pairing retry {0}'.format(retry))
            self._cmdresp('AT+JCCR={0},01'.format(mac))
            for _ in range(10):
                line = self._readline()
                if line == '':
                    continue
                # Device we are pairing to has asked for a pin code
                if line[:6] == '+RPCI=':
                    self._log('Sending PIN')
                    self._cmdresp('AT+JPCR=04,{0}'.format(pin))
                    continue
                # Device we are pairing to has asked to verify 6 digit id
                if line[:6] == '+RUCE=':
                    self._log('Sending confirmation')
                    self._cmdresp('AT+JUCR=1')
                    continue
                # Example of good pairing response: '+RCCRCNF=500,0000,0'
                # The first 500 is MTU and is 000 on error.
                # The ',0' means good status and ',1' would be an error.
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
        raise BtRadioError('Unable to pair with device')

    def unpair(self):
        """Unpair with bluetooth device."""
        self._log('Unpairing')
        self._cmdresp('AT+JSDR')
        for _ in range(self.unpair_retries):
            time.sleep(2)
            line = self._readline()
            if line == '':
                continue
            if line == '+RDII':     # good unpairing response
                self._log('Now Un-Paired.')
                return
        raise BtRadioError('Unpairing timed out')

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
            raise BtRadioError('JSON-RPC requires streaming data mode')
        if params is None:
            params = {}
        request = {
            'jsonrpc': '2.0',
            'id': 8256,
            'method': method,
            'params': params,
            }
        cmd = json.dumps(request)
        self._log('JSONRPC request: {0!r}'.format(cmd))
        self.port.flushInput()
        self._write(cmd + '\r')
        response = self._readline()
        return json.loads(response)['result']
