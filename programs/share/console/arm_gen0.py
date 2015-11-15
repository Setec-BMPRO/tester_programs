#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 & SX-750 ARM processor console driver.

Communication via SimSerial port to the ARM processor.

"""

import time
import logging

from . import tester


# Line terminator
_EOL = b'\r'
# Timeouts
_READ_TMO = 0.1
_LINE_TMO = 4.0
# Time to allow for a Non-Volatile memory write to complete
_NV_DELAY = 0.5


class ConsoleGen0():

    """Communications to ARM console."""

    def __init__(self, port):
        """Initialise communications.

        @param port SimSerial port to use

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        port.timeout = _READ_TMO
        self._port = port
        self._limit = tester.testlimit.LimitBoolean('SerialTimeout', 0, False)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor, StrKill ))
        self._data = {
            'ARM-AcDuty':
                (self._getvalue, ('X-AC-DETECTOR-DUTY', 1, '%')),
            'ARM-AcPer':
                (self._getvalue, ('X-AC-DETECTOR-PERIOD', 0.001, 'ms')),
            'ARM-AcFreq':
                (self._getvalue, ('X-AC-LINE-FREQUENCY', 1, 'Hz')),
            'ARM-AcVolt':
                (self._getvalue, ('X-AC-LINE-VOLTS', 1, 'Vrms')),
            'ARM-PfcTrim':
                (self._getvalue, ('X-PFC-TRIM', 1, '%')),
            'ARM-12VTrim':
                (self._getvalue, ('X-CONVERTER-VOLTS-TRIM', 1, '%')),
            'ARM-5V':
                (self._getvalue, ('X-RAIL-VOLTAGE-5V', 0.001, 'mV')),
            'ARM-12V':
                (self._getvalue, ('X-RAIL-VOLTAGE-12V', 0.001, 'mV')),
            'ARM-24V':
                (self._getvalue, ('X-RAIL-VOLTAGE-24V', 0.001, 'mV')),
            'ARM-5Vadc':
                (self._getvalue, ('X-ADC-5V-RAIL', 1, 'Counts')),
            'ARM-12Vadc':
                (self._getvalue, ('X-ADC-12V-RAIL', 1, 'Counts')),
            'ARM-24Vadc':
                (self._getvalue, ('X-ADC-24V-RAIL', 1, 'Counts')),
            'ARM_SwVer':
                (self.version, None),
            }

    def open(self):
        """Open port."""
        self._logger.debug('Open')
        self._port.open()

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Put a string into the read-back buffer.

        @param string_data Data string, or tuple of data strings.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to put in front of the buffer.
        Note: _FLUSH is a marker to stop the flush of the data buffer.

        """
        self._port.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Close serial communications."""
        self._logger.debug('Close')
        self._port.close()

    def configure(self, cmd):
        """Sensor: Configure for next reading."""
        self._read_cmd = cmd

    def opc(self):
        """Sensor: Dummy OPC."""
        pass

    def read(self):
        """Sensor: Read ARM data.

        @return Value

        """
        self._logger.debug('read %s', self._read_cmd)
        fn, param = self._data[self._read_cmd]
        result = fn(param)
        self._logger.debug('result %s', result)
        return result

    def _getvalue(self, data):
        """Get data value from ARM.

        @return Value

        """
        cmd, scale, strkill = data
        reply = self._sendrecv('{} X?'.format(cmd))
        if reply is None:
            reply = 'NaN'
        reply = reply.replace(strkill, '')
        value = float(reply) * scale
        return value

    def defaults(self):
        """Write defaults into NV memory."""
        self._logger.debug('Defaults')
        self.unlock()
        self._nvwrite()

    def unlock(self):
        """Unlock the ARM and turn echo off."""
        self._logger.debug('Unlock')
        self._flushInput()
        self._sendrecv('0 ECHO')
        self._sendrecv('$DEADBEA7 UNLOCK')

    def _nvwrite(self):
        """Perform NV Memory Write."""
        self._sendrecv('NV-WRITE')
        time.sleep(_NV_DELAY)

    def version(self, param=None):
        """Return software version."""
        ver = self._sendrecv('X-SOFTWARE-VERSION x?').strip()
        bld = self._sendrecv('X-BUILD-NUMBER x?').strip()
        verbld = '.'.join((ver, bld))
        self._logger.debug('Version is %s', verbld)
        return verbld

    def cal_pfc(self, voltage):
        """Calibrate PFC voltage.

        420000 CAL-PFC-BUS-VOLTS        (V in mV)
        NV-WRITE

        """
        self._logger.debug('CalPFC %s', voltage)
        cmd = '{} CAL-PFC-BUS-VOLTS'.format(int(voltage * 1000))
        self._sendrecv(cmd)
        self._nvwrite()

    def cal_12v(self, voltage):
        """Calibrate 12V output (GEN8 only).

        12000 CAL-CONVERTER-VOLTS       (V in mV)
        NV-WRITE

        """
        self._logger.debug('Cal12v %s', voltage)
        cmd = '{} CAL-CONVERTER-VOLTS'.format(int(voltage * 1000))
        self._sendrecv(cmd)
        self._nvwrite()

    def _flushInput(self):
        """Flush input (serial port and buffer)."""
        self._logger.debug('FlushInput')
        self._port.flushInput()
        self._buf = b''

    def _sendrecv(self, command):
        """Send a command, and read the response line.

        @return Reply string

        """
        self._writeline(command)
        reply = self._readline()
        if reply is None:
            self._logger.debug('Timeout after %s', command)
            self._limit.check(True, position=1)
        return reply

    def _readline(self):
        """Read a _EOL terminated line from the ARM.

        Return string, with the _EOL removed.
        Upon read timeout, return None.

        """
        tries = 0
        while True:
            self._buf += self._port.read(512)
            pos = self._buf.find(_EOL)
            if pos >= 0:
                line, self._buf = self._buf[:pos], self._buf[pos + 1:]
                break
            tries += 1
            if tries * _READ_TMO > _LINE_TMO:
                line = None
                break
        self._logger.debug('Decode line: %s', repr(line))
        return line if line is None else line.decode(errors='ignore')

    def _writeline(self, line):
        """Write a _EOL terminated line to the ARM."""
        self._logger.debug('Send line: %s', repr(line))
        self._port.write(line.encode() + _EOL)
