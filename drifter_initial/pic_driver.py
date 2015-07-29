#!/usr/bin/env python3
"""Drifter Initial PIC processor console driver.

Communication via Serial port to the PIC processor.

"""

import serial
import time
import logging

import tester


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

    """PIC console data exposed as a Sensor."""

    def __init__(self, pic, key, rdgtype=tester.sensor.Reading, position=1):
        """Create sensor."""
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
        """Take a reading.

        @return Reading

        """
        rdg = self._rdgtype(value=super().read(), position=self.position)
        return (rdg, )


class Console():

    """Communications to PIC console."""

    def __init__(self, port=0, baud=9600):
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
            'PIC-NvStatus': (self._getvalue,
                             ('nv-status PRINT', 1)),
            'PIC-ZeroCheck': (self._getvalue,
                              ('x-current-filtered x?', 1)),
            'PIC-Vin':      (self._getvalue,
                             ('x-volts-filtered x?', _VOLTAGE_SCALE)),
            'PIC-Isense':   (self._getvalue,
                             ('x-current-filtered x?', _CURRENT_SCALE)),
            'PIC-Vfactor':  (self._getvalue,
                             ('x-cal-factor-volts x?', 1)),
            'PIC-Ifactor':  (self._getvalue,
                             ('x-cal-factor-current x?', 1)),
            'PIC-Ioffset':  (self._getvalue,
                             ('x-cal-offset-current x?', 1)),
            'PIC-Ithreshold': (self._getvalue,
                               ('x-zero-current-display-threshold x?', 1)),
            }

    def open(self):
        """Open serial communications."""
        self._logger.debug('Open')
        if self._ser is None:
            self._ser = serial.Serial(
                self._port, self._baud, timeout=_READ_TMO)
        self._flushInput()

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
        """Sensor: Read PIC data.

        @return Data

        """
        self._logger.debug('read %s', self._read_cmd)
        fn, param = self._data[self._read_cmd]
        result = fn(param)
        self._logger.debug('result %s', result)
        return result

    def _getvalue(self, data):
        """Get data value from PIC.

        @return Data

        """
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
        self._sendrecv('nv-write-default restart', delay=4)
        self.unlock()
        self._nvwrite()

    def unlock(self):
        """Unlock the PIC and turn echo off."""
        self._logger.debug('Unlock')
        self._flushInput()
        self._sendrecv('1 hosted')
        self._sendrecv('xdeadbea7 unlock', delay=0.1)

    def _nvwrite(self):
        """Perform NV Memory Write."""
        self._sendrecv('nv-write', delay=5)

    def aps_disable(self):
        """Turn off analogue power switching for testing."""
        self._logger.debug('Disable aps')
        self._sendrecv('1 aps-disable')

    def offset(self):
        """Set offset values."""
        self._logger.debug('Set offset values')
        self._sendrecv('-8 X-CAL-OFFSET-CURRENT X!', delay=0.1)
        self._sendrecv('160 X-ZERO-CURRENT-DISPLAY-THRESHOLD X!', delay=0.1)
        self._nvwrite()

    def cal_reload(self):
        """Update internal filters."""
        self._logger.debug('Cal reload')
        self._sendrecv('cal-reload', delay=10)

    def cal_zero_curr(self):
        """Calibrate zero battery current."""
        self._logger.debug('CalZeroCurr')
        self._sendrecv('cal-i-zero')
        self._nvwrite()

    def cal_volts(self, voltage):
        """Calibrate battery voltage.

        12000 {} cal-v-slope        (V in mV)

        """
        self._logger.debug('CalVolts %s', voltage)
        cmd = '{} cal-v-slope'.format(int(round(voltage / _VOLTAGE_SCALE)))
        self._sendrecv(cmd)
        self._nvwrite()

    def cal_curr(self, sense_amps):
        """Calibrate battery current.

        90000 {} cal-i-slope       (V in uV)

        """
        self._logger.debug('CalCurr %s', sense_amps)
        cmd = '{} cal-i-slope'.format(int(round(sense_amps / _CURRENT_SCALE)))
        self._sendrecv(cmd)
        self._nvwrite()

    def _flushInput(self):
        """Flush input (serial port and buffer)."""
        if self._ser is not None:
            self._buf += self._ser.read(512)
            self._ser.flushInput()
        if len(self._buf) > 0:
            self._logger.debug('_flushInput() %s', self._buf)
        self._buf = b''

    def _sendrecv(self, command, delay=0):
        """Send a command, and read the response line.

        @return Command reply

        """
        self._flushInput()
        self._writeline(command)
        if self._ser is not None:
            try:
                reply = self._readline()
            except TimeoutError:
                self._flushInput()
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

        @return string, with the _EOL removed, None for read timeout

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
        if self._ser is not None:
            self._ser.write(line.encode() + _EOL)
            time.sleep(delay)
