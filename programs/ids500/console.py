#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 PIC processor console driver.

Communication via Serial port to the PIC processor.

"""

import time
import logging
import re
import sensor
from testlimit import LimitBoolean

# Line terminator
_EOL = b'\r\n'
# Timeouts
_READ_TMO = 0.1
_LINE_TMO = 4.0


class TimeoutError(Exception):

    """Read line Timeout."""


class HwVerError(Exception):

    """Hardware Version Error."""


class Sensor(sensor.Sensor):

    """PIC console data exposed as a Sensor."""

    def __init__(self, pic, key, rdgtype=sensor.Reading, position=1):
        super().__init__(pic, position)
        self._pic = pic
        self._key = key
        self._rdgtype = rdgtype
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created')

    def configure(self):
        """Configure measurement."""
        self._pic.configure(self._key)

    def read(self):
        """Take a reading."""
        rdg = self._rdgtype(value=super().read(), position=self.position)
        return (rdg, )


class ConsoleResult():

    """Representation of a data string from the console."""

    def __init__(self, data):
        self.type, self.index, self.value, self.text = (None, None, None, None)
        if data[0:2] in ('I,', 'D,', 'S,'):
            data = data.replace(' ', '')
            result = data.split(',')
            self.type = result[0]
            self.index = result[1]
            self.value = result[2]
            self.text = result[3]
        else:
            self.value = data


class Console():

    """A console "instrument" to communicate with the PIC."""

    def __init__(self, serport):
        """Open serial communications."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._serport = serport
        self._buf = b''
        self._limit = LimitBoolean('SerialTimeout', 0, False)
        self._read_cmd = None
        # Data readings:
        # Name -> (function, Command))
        self._data = {
            'PIC-SwTstMode': (self._getstring, None),
            'PIC-HwVerCheck': (self._getstring, '?,I,2'),
            'PIC-SerCheck': (self._getstring, '?,I,3'),
            'PIC-SwRev': (self._getstring, '?,I,1'),
            'PIC-MicroTemp': (self._getstring, '?,D,16'),
            }

    def configure(self, cmd):
        """Sensor: Configure for next reading."""
        self._read_cmd = cmd

    def opc(self):
        """Sensor: Dummy OPC."""
        pass

    def read(self):
        """Sensor: Read PIC data."""
        self._logger.debug('read %s', self._read_cmd)
        fn, param = self._data[self._read_cmd]
        data = fn(param)
        result = ConsoleResult(data)
        self._logger.debug('result value: %s', result.value)
        return result.value

    def _getstring(self, cmd):
        """Get data string from PIC."""
        return self._sendrecv(cmd)

    def sw_test_mode(self):
        """Enter software Test Mode."""
        self._logger.debug('Software Test Mode')
        self._writeline('?,?')
        self._writeline('?,?')
        self._flushInput()
        self._writeline('S,:,0', )
        self._flushInput()
        self._writeline('S,:,2230')
        self._flushInput()
        self._writeline('S,:,42')

    def write_hwver(self, hwver):
        """Write Hardware Version into memory."""
        self._logger.debug('Write Hardware Version')
        pattern = r'^[0-9][0-9][A-Z]$'
        match = re.search(pattern, hwver)
        if not match:
            raise HwVerError('Hardware Rev Number must be in the form 01A' +
                             ' (2 digits, then a letter)')
        self._writeline('S,@,{}'.format(hwver))
        self._flushInput()

    def write_ser(self, sernum):
        """Write Serial Number into memory."""
        self._logger.debug('Write Serial Number')
        self._writeline('S,#,{}'.format(sernum))
        reply = self._readline()
        match = re.search(r'Setting is Protected', reply)
        if match:
            self._logger.warning('Cannot write Serial!(Protected)')

    def _flushInput(self):
        """Flush input (serial port and buffer)."""
        if not self._serport is None:
            self._buf += self._serport.read(512)
            self._serport.flushInput()
        if len(self._buf) > 0:
            self._logger.debug('_flushInput() %s', self._buf)
        self._buf = b''

    def _sendrecv(self, command, delay=0):
        """Send a command, and read the response line."""
        if command:
            self._writeline(command)
        if not self._serport is None:
            try:
                reply = self._readline()
            except TimeoutError:
                self._writeline(command)
                try:
                    reply = self._readline()
                except TimeoutError:
                    self._logger.debug('Timeout after %s', command)
                    self._limit.check(True, 1)
                    return
            time.sleep(delay)
            return reply

    def _readline(self):
        """
        Read a _EOL terminated line from the PIC.

        Return string, with the _EOL removed.
        Upon read timeout, return None.

        """
        tries = 0
        while True:
            self._buf += self._serport.read(512)
            pos = self._buf.find(_EOL)
            if pos >= 0:
                self._logger.debug('EOL match at %s in %s', pos, self._buf)
                line, self._buf = self._buf[:pos], self._buf[pos + 2:]
                break
            tries += 1
            if tries * _READ_TMO > _LINE_TMO:
                self._logger.debug('Timeout. Buffer=%s', self._buf)
                raise TimeoutError
        self._logger.debug('Line=%s, Buffer=%s', line, self._buf)
        self._flushInput()
        return line.decode()

    def _writeline(self, line, delay=0):
        """Write a _EOL terminated line to the PIC."""
        if not self._serport is None:
            self._logger.debug('writeline: %s', repr(line))
            self._serport.write(line.encode() + _EOL)
            time.sleep(delay)
