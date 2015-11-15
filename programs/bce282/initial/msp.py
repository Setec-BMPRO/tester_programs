#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Initial MSP430F2272 processor console driver.

Communication via Serial port to the MSP430F2272 processor.

"""

import serial
import time
import logging

import tester.testlimit


# Line terminator
_EOL = b'\r'
# Timeouts
_READ_TMO = 0.1
_LINE_TMO = 4.0
_VOLTAGE_SCALE = 0.001
_CURRENT_SCALE = 0.001

# FIXME: Add _VOLTAGE_SCALE here


class TimeoutError(Exception):
    """Read line Timeout."""


class Sensor(tester.sensor.Sensor):

    """MSP430 console data exposed as a Sensor."""

    def __init__(self, msp, key, rdgtype=tester.sensor.Reading, position=1):
        super().__init__(msp, position)
        self._msp = msp
        self._key = key
        self._rdgtype = rdgtype
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created')

    def configure(self):
        """Configure measurement."""
        self._msp.configure(self._key)

    def read(self):
        """Take a reading."""
        rdg = self._rdgtype(value=super().read(), position=self.position)
        return (rdg, )


class Console():

    """Communications to MSP430 console."""

    def __init__(self, port=0, baud=57600):
        """Open serial communications."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._port = port
        self._baud = baud
        self._ser = None
        self._buf = b''
        self._limit = tester.testlimit.LimitBoolean('SerialTimeout', 0, False)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor ))
        self._data = {
            'MSP-NvStatus': (self._getvalue,
                             ('nv-status PRINT', 1)),
            'MSP-Vout':      (self._getvalue,
                             ('x-supply-voltage x@ print', _VOLTAGE_SCALE)),
            'MSP-Iout':      (self._getvalue,
                             ('x-supply-current x@ print', _CURRENT_SCALE)),
            }

    def open(self):
        """Open serial communications."""
        self._logger.debug('Open')
        if self._ser is None:
            self._ser = serial.Serial(self._port, self._baud,
                                      timeout=_READ_TMO)
        time.sleep(1)
        self._flush()

    def close(self):
        """Close serial communications."""
        self._logger.debug('Close')
        if self._ser is None:
            return
        try:
            self._ser.close()
            self._ser = None
        except Exception:
            pass

    def configure(self, cmd):
        """Sensor: Configure for next reading."""
        self._read_cmd = cmd

    def opc(self):
        """Sensor: Dummy OPC."""
        pass

    def read(self):
        """Sensor: Read MSP430 data."""
        self._logger.debug('read %s', self._read_cmd)
        fn, param = self._data[self._read_cmd]
        result = fn(param)
        self._logger.debug('result %s', result)
        return result

    def _getvalue(self, data):
        """Get data value from MSP430."""
        cmd, scale = data
        reply = self._sendrecv(cmd)
        try:
            value = float(reply) * scale
        except ValueError:
            self._logger.debug('Reply from console: %s', reply)
            value = 10e99
        return value

    def defaults(self):
        """Write defaults into NV memory."""
        self._logger.debug('Defaults')
        self.unlock()
        self._sendrecv('nv-factory-write restart', delay=1)
        self.unlock()

    def unlock(self):
        """Unlock the MSP430 and turn echo off."""
        self._logger.debug('Unlock')
        self._flush()
        self._sendrecv('0 echo')
        self._sendrecv('xdeadbea7 unlock', delay=0.5)

    def test_mode_enable(self):
        """Disable some software functions for testing."""
        self._logger.debug('Enable test mode')
        self._sendrecv('test-mode-enable')

    def bsl_passwd(self):
        """Dump existing password."""
        self._logger.debug('Dump password')
        self._flush()
        self._sendrecv('0 echo')
        reply = self._sendrecv('bsl-password')
        return reply

    def filter_reload(self):
        """Reset internal filters."""
        self._logger.debug('Filter reload')
        self._sendrecv('adc-filter-reload', delay=1)

    def _nvwrite(self):
        """Perform NV Memory Write."""
        self._sendrecv('nv-factory-write', delay=0.1)

    def _flush(self):
        """Flush input (serial port and buffer)."""
        if not self._ser is None:
            self._buf += self._ser.read(512)
            self._ser.flushInput()
        if len(self._buf) > 0:
            self._logger.debug('_flush() %s', self._buf)
        self._buf = b''

    def _sendrecv(self, command, delay=0):
        """Send a command, and read the response line."""
        self._flush()
        self._writeline(command)
        if not self._ser is None:
            try:
                reply = self._readline()
            except TimeoutError:
                self._flush()
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
        """Read a _EOL terminated line from the PIC.

        Return string, with the _EOL removed.
        Upon read timeout, return None.

        """
        tries = 0
        while True:
            self._buf += self._ser.read(512)
            pos = self._buf.find(_EOL)
            if pos >= 0:
                self._logger.debug('EOL match at %s in %s', pos, self._buf)
                line, self._buf = self._buf[:pos], self._buf[pos + 1:]
                break
            tries += 1
            if tries * _READ_TMO > _LINE_TMO:
                self._logger.debug('Timeout. Buffer=%s', self._buf)
                raise TimeoutError
        return line.decode()

    def _writeline(self, line, delay=0.001):
        """Write a _EOL terminated line to the PIC."""
        self._logger.debug('writeline: %s', repr(line))
        if not self._ser is None:
            self._ser.write(line.encode() + _EOL)
            time.sleep(delay)
