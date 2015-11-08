#!/usr/bin/env python3
"""2nd Generation ARM Processor Console Driver.

Communication is done with a Serial port to the ARM processor.

Commands are sent, followed by a '\r' trigger character.

This console works well with echo off, as it has a configurable command prompt.
We set a prompt that ends in a newline, so we can just call readline() to
read all responses.

Implements the methods to expose ARM readings as Sensors.

"""

import logging
import time

from ._base import ConsoleError
from . import tester

# Command termination character
_CMD_RUN = b'\r'
# Custom command prompt set on the console interface
_CMD_PROMPT = 'OK'


class ConsoleGen2():

    """Communications to Second Generation ARM console."""

    def __init__(self, port):
        """Initialise communications.

        @param port SimSerial port to use

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        port.timeout = 1000 / port.baudrate  # Timeout of 100 Bytes
        self._port = port
        self._read_key = None
        self.cmd_data = {}  # Data readings: Key=Name, Value=Parameter

    def open(self):
        """Open port."""
        self._port.open()
        # Set a prompt that ends with a newline, so we can use readline()
        self.action('{} PROMPT'.format(_CMD_PROMPT + r'\n'))
        self.action('0 ECHO')       # No console echo
        self._port.flushInput()

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
        """Close serial port."""
        self._port.close()

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def opc(self):
        """Sensor: Dummy OPC."""
        pass

    def read(self):
        """Sensor: Read ARM data using the last defined key.

        @return Value

        """
        return self[self._read_key]

    def __getitem__(self, key):
        """Read a value from the ARM.

        @return Reading ID

        """
        try:
            parameter = self.cmd_data[key]
            reply = parameter.read(self.action)
        except ConsoleError:
            # Sensor uses this, so we must always return a valid reading
            reply = parameter.error_value
        return reply

    def __setitem__(self, key, value):
        """Write a value to the ARM.

        @param key Reading ID
        @param value Data value.

        """
        try:
            parameter = self.cmd_data[key]
            parameter.write(value, self.action)
        except ConsoleError:
# FIXME: This does not setup the test results properly.
#   We should be sending a TestLimit fail signal...
            # This will make the unit fail the test
            raise tester.measure.MeasurementFailedError

    def defaults(self, hwver=None, sernum=None):
        """Write factory defaults into NV memory.

        @param hwver Tuple (Major [1-255], Minor [1-255], Mod [character]).
        @param sernum Serial number string.

        """
        self._logger.debug('Write factory defaults')
        self.unlock()
        self.action('{0[0]} {0[1]} "{0[2]} SET-HW-VER'.format(hwver))
        self.action('"{} SET-SERIAL-ID'.format(sernum))
        self.action('NV-DEFAULT')
        self.nvwrite()

    def unlock(self):
        """Unlock the ARM."""
        self._logger.debug('Unlock')
        self.action('$DEADBEA7 UNLOCK')

    def nvwrite(self):
        """Perform NV Memory Write."""
        self._logger.debug('NV-Write')
        self.action('NV-WRITE', delay=0.5)

    def version(self):
        """Return software version."""
        verbld = self.action('SW-VERSION?', expected=1)
        self._logger.debug('Version is %s', verbld)
        return verbld

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response line(s).

        @param command Command string.
        @param expected Expected number of responses.
        @param delay Delay between sending command and reading response.
        @return Response (a List of received line Strings).

        """
        if command:
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected)

    def _write_command(self, command):
        """Write a command.

        If echo is enabled, the echo of each command character sent is
        read back. The echo of _CMD_RUN is NOT expected, or read.

        @param command Command string.
        @raises ConsoleError if the command does not echo.

        """
        self._logger.debug('--> %s', repr(command))
        cmd_data = command.encode()
        self._port.write(cmd_data + _CMD_RUN)

    def _read_response(self, expected):
        """Read a response.

        Keep reading until we get a _CMD_PROMPT.
        @param expected Expected number of responses.
        @return Response (None / String / List of Strings).
        @raises ConsoleError If not enough response strings are seen.

        """
        response = []
        last_response = ''
        while last_response != _CMD_PROMPT:
            last_response = self._port.readline()
            self._logger.debug('<--- %s', repr(last_response))
            if last_response is None:
                raise ConsoleError('No response')
            last_response = last_response.decode(errors='ignore')
            if last_response != _CMD_PROMPT:
                response.append(last_response)
        response_count = len(response)
        if response_count == 0:     # No response -> None
            response = None
        if response_count == 1:     # 1 response -> String
            response = response[0]
        self._logger.debug('<-- %s', repr(response))
        if response_count < expected:
            raise ConsoleError(
                'Expected {}, actual {}'.format(expected, response_count))
        return response
