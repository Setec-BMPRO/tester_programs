#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck communications to ARM processor.

Communication via Serial port to the ARM processor.

Values:
    SW-VERSION?             (M.N.OOOO)
    SET-SERIAL-ID           (XXXXXXXXXXX)
    X-BATTERY-VOLTS X?      (mV)
    X-BATTERY-CURRENT X?    (mA)
    BT-MAC?                 (MAC address as 12 Hex digits)

"""

import logging
import time

import tester


# Line terminators
_EOL_IN = b'\n'
_EOL_OUT = b'\r'
# Inter-character pause when sending (sec)
_ICP = 0.1
# Delay to allow NV-WRITE to complete
_NVW = 1.0
# Timeouts (sec)
_READ_TMO = 2.0


class Sensor(tester.sensor.Sensor):

    """ARM console data exposed as a Sensor."""

    def __init__(self, arm, key, rdgtype=tester.sensor.Reading, position=1):
        """Create sensor."""
        super().__init__(arm, position)
        self._arm = arm
        self._key = key
        self._rdgtype = rdgtype

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

    """Communications link to ARM console."""

    def __init__(self, port):
        """Open serial communications."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._ser = port
        # Limit used to record timeouts as fail readings
        self._limit = tester.testlimit.LimitBoolean('SerialTimeout', 0, False)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor, StrKill ))
        self._data = {
            'ARM_Volt': (self._getvalue,
                         ('X-BATTERY-VOLTS', 0.001, 'mV')),
            'ARM_Curr': (self._getvalue,
                         ('X-BATTERY-CURRENT', 0.001, 'mA')),
            'ARM_SwVer': (self.version, None),
            'ARM_Mac': (self.mac, None),
            }

    def open(self):
        """Open serial communications."""
        self._logger.debug('Open')
        self._ser.timeout = _READ_TMO
        self._ser.open()

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Put a string into the read-back buffer.

        @param string_data Data string, or tuple of data strings.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to put in front of the buffer.
        Note: _FLUSH is a marker to stop the flush of the data buffer.

        """
        self._ser.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Close serial communications."""
        self._logger.debug('Close')
        self._ser.close()

    def configure(self, cmd):
        """Sensor: Configure for next reading."""
        self._read_cmd = cmd

    def opc(self):
        """Sensor: Dummy OPC."""
        pass

    def read(self):
        """Sensor: Read ARM data.

        @return Reading

        """
        self._logger.debug('read %s', self._read_cmd)
        fn, param = self._data[self._read_cmd]
        result = fn(param)
        self._logger.debug('result %s', result)
        return result

    def _getvalue(self, data):
        """Get data value from ARM.

        @return Reading

        """
        cmd, scale, strkill = data
        reply = self._sendrecv('{} X?'.format(cmd))
        if reply is None:
            value = -999.999
        else:
            reply = reply.replace(strkill, '')
            value = float(reply) * scale
        return value

    def defaults(self):
        """Write defaults into NV memory."""
        self._logger.debug('Defaults')
        self.unlock()
        self._sendrecv('NV-WRITE')
        time.sleep(_NVW)     # Allow the NV memory write to complete

    def unlock(self):
        """Unlock the ARM and turn echo off."""
        self._logger.debug('Unlock')
        self._sendrecv('$DEADBEA7 UNLOCK')

    def version(self, param=None):
        """Return software version.

        @return Version string

        """
        ver = self._sendrecv('SW-VERSION?').strip()
        self._logger.debug('Version is %s', ver)
        return ver

    def set_serial(self, number):
        """Set the serial number of the ARM."""
        self._sendrecv('SET-SERIAL-ID ' + number)
        self._sendrecv('NV-WRITE')
        time.sleep(_NVW)     # Allow the NV memory write to complete

    def mac(self, param=None):
        """Read the Bluetooth MAC adderess.

        @return MAC address

        """
        mac = self._sendrecv('BT-MAC?').strip()
        parts = []
        for i in range(0, 12, 2):
            parts.append(mac[i:i+2])
        mac = ':'.join(parts)
        self._logger.debug('MAC address is %s', mac)
        return mac

    def alarm(self, new_state):
        """Turn alarm relay on (True) or off (False)."""
        # Disable alarm process so it won't switch the relay back
        self._sendrecv('4 X-SYSTEM-ENABLE X!')
        cmd = '{} ALARM-RELAY'.format(1 if new_state else 0)
        self._sendrecv(cmd)

    def _sendrecv(self, command):
        """Send a command, and read the response line.

        @return Response

        """
        self._logger.debug('writeline() "%s"', command)
        self._writeline(command)
        reply = self._readline()
        if reply is None:
            self._logger.debug('Timeout after "%s"', command)
            self._limit.check(True, 1)
        if reply == 'Error: unknown command.':
            self._logger.debug('Unknown command error for "%s"', command)
            self._limit.check(True, 1)
        return reply

    def _readline(self):
        """Read a _EOL_IN terminated line from the ARM.

        Return string, with the _EOL_IN removed.

        """
        line = self._ser.read(1000)
        if len(line) == 0:      # if the earlier _EOL_OUT was missed
            self._logger.debug('readline() resend %s', repr(_EOL_OUT))
            self._ser.write(_EOL_OUT)
            line = self._ser.read(1000)
        try:
            line = line.decode()
        except:
            self._logger.warning('readline() decode error %s', repr(line))
            line = ''
        self._logger.debug('readline() raw %s', repr(line))
        line = line.replace('\r\n> ', '').replace('\7', '')
        line = line.replace(' -> ', '')
        self._logger.debug('readline() clean %s', repr(line))
        return line

    def _writeline(self, line):
        """Write a _EOL terminated line to the ARM.

        Echo is left on so we can confirm reception of each character by seeing
        the echo response.
        Sometimes the unit will send a start bit, then go to sleep for about
        6ms, before completing the transmitted byte. The PC sees that as two
        different binary bytes.
        This console implementation sucks...

        """
        self._ser.flushInput()
        for char in line:
            retry = 0
            while True:
                retry += 1
                if retry > 10:
                    self._logger.debug('writeline() error on "%s"', line)
                    self._limit.check(True, 1)
                    return
                self._ser.write(char.encode())
                res = self._ser.read(1)
                try:
                    res = res.decode()
                except:
                    self._logger.warning('readline() decode error "%s"',
                                         repr(res))
                    res = ''
                if char == res:
                    break
                else:
                    self._logger.debug('writeline() echo error %s vs %s in %s',
                                       repr(res), repr(char), repr(line))
                    time.sleep(0.1)     # wait for any delayed transmission
                    self._ser.flushInput()  # then flush it away
        self._ser.write(_EOL_OUT)
