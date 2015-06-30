#!/usr/bin/env python3
"""Trek2 ARM processor console driver.

Communication via Serial port to the ARM processor.

"""

import time
import logging

import tester

# Line terminator
_EOL = b'\n'
# Timeouts
_READ_TMO = 0.1
_LINE_TMO = 4.0


class TimeoutError(Exception):

    """Read line Timeout."""


class Sensor(tester.sensor.Sensor):

    """ARM console data exposed as a Sensor."""

    def __init__(self, arm, key, rdgtype=tester.sensor.Reading, position=1):
        """Create a sensor."""
        super().__init__(arm, position)
        self._arm = arm
        self._key = key
        self._rdgtype = rdgtype
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created')

    def configure(self):
        """Configure measurement."""
        self._arm.configure(self._key)

    def read(self):
        """Take a reading.

        @return Reading

        """
        rdg = self._rdgtype(value=super().read(), position=self.position)
        return (rdg, )


class Console():

    """Communications to ARM console."""

    def __init__(self, serport):
        """Open serial communications."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._serport = serport
        self._buf = b''
        self._serport.flushInput()
        self._limit = tester.testlimit.LimitBoolean('SerialTimeout', 0, False)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor, StrKill ))
        self._data = {
            'ARM-AcDuty':  (self._getvalue,
                            ('X-AC-DETECTOR-DUTY', 1, '%')),
            'ARM-AcPer':   (self._getvalue,
                            ('X-AC-DETECTOR-PERIOD', 0.001, 'ms')),
            'ARM-AcFreq':  (self._getvalue,
                            ('X-AC-LINE-FREQUENCY', 1, 'Hz')),
            'ARM-AcVolt':  (self._getvalue,
                            ('X-AC-LINE-VOLTS', 1, 'Vrms')),
            'ARM-PfcTrim': (self._getvalue,
                            ('X-PFC-TRIM', 1, '%')),
            'ARM-12VTrim': (self._getvalue,
                            ('X-CONVERTER-VOLTS-TRIM', 1, '%')),
            'ARM-5V':      (self._getvalue,
                            ('X-RAIL-VOLTAGE-5V', 0.001, 'mV')),
            'ARM-12V':     (self._getvalue,
                            ('X-RAIL-VOLTAGE-12V', 0.001, 'mV')),
            'ARM-24V':     (self._getvalue,
                            ('X-RAIL-VOLTAGE-24V', 0.001, 'mV')),
            'ARM-5Vadc':   (self._getvalue,
                            ('X-ADC-5V-RAIL', 1, 'Counts')),
            'ARM-12Vadc':  (self._getvalue,
                            ('X-ADC-12V-RAIL', 1, 'Counts')),
            'ARM-24Vadc':  (self._getvalue,
                            ('X-ADC-24V-RAIL', 1, 'Counts')),
            'ARM_SwVer':   (self.version, None),
            }

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
            value = -999.999
        else:
            reply = reply.replace(strkill, '')
            value = float(reply) * scale
        return value

    def defaults(self, hwver, sernum):
        """Write factory defaults into NV memory."""
        self._logger.debug('Write factory defaults')
        self.unlock()
        self._sendrecv('{} “ SET-HW-VER'.format(hwver))
        self._sendrecv('“{} SET-SERIAL-ID'.format(sernum))
        self._sendrecv('NV-DEFAULT')
        self._nvwrite()
        self._sendrecv('RESTART')

    def unlock(self):
        """Unlock the ARM."""
        self._logger.debug('Unlock')
#        self._flush()
        self._sendrecv('$DEADBEA7 UNLOCK')

    def _nvwrite(self):
        """Perform NV Memory Write."""
        self._sendrecv('NV-WRITE')
        if self._serport is not None:
            time.sleep(0.5)     # Allow the NV memory write to complete

    def bklght(self, param=None):
        """Turn backlight on/off."""
        self._writeline('{} 5 X!'.format(param))

    def version(self, param=None):
        """Return software version."""
        ver = self._sendrecv('X-SOFTWARE-VERSION x?').strip()
        bld = self._sendrecv('X-BUILD-NUMBER x?').strip()
        verbld = '.'.join((ver, bld))
        self._logger.debug('Version is %s', verbld)
        return verbld

    def _flush(self):
        """Flush input (serial port and buffer)."""
        if not self._serport is None:
            self._buf += self._serport.read(512)
            self._serport.flushInput()
        if len(self._buf) > 0:
            self._logger.debug('_flush() %s', self._buf)
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
        Read a _EOL terminated line from the ARM.

        Return string, with the _EOL removed.
        Upon read timeout, return None.

        """
        tries = 0
        while True:
            self._buf += self._serport.read(512)
            pos = self._buf.find(_EOL)
            if pos >= 0:
                self._logger.debug('EOL match at %s in %s', pos, self._buf)
                line, self._buf = self._buf[:pos], self._buf[pos + 1:]
                break
            tries += 1
            if tries * _READ_TMO > _LINE_TMO:
                self._logger.debug('Timeout. Buffer=%s', self._buf)
                raise TimeoutError
        self._logger.debug('Line=%s, Buffer=%s', line, self._buf)
#        self._flush()
        return line.decode()

    def _writeline(self, line, delay=0):
        """Write a _EOL terminated line to the ARM."""
        if not self._serport is None:
            self._logger.debug('writeline: %s', repr(line))
            self._serport.write(line.encode() + _EOL)
            time.sleep(delay)

