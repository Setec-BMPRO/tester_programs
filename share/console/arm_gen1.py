#!/usr/bin/env python3
"""1st Generation ARM Processor Console Driver.

Communication is done with a Serial port to the ARM processor.

Commands are sent, followed by a '\r' trigger character.
    Each character of the command is echoed as it is sent.
    The '\r' is not echoed as it is sent, as there are often other response
    characters before and after the '\r'...
    The LPC1549 device does NOT have a buffered UART, so a character cannot
    be sent until the previous one has been echoed back.

After a command has been sent, the string ' -> ' is (usually?) sent back,
followed by any command response, and then followed by '\r\n> '.
That is the line termination of CR LF, then a user prompt of '> '.
For example:
    A command with no return value: 'NV-DEFAULT'
    will return the echo and response: 'NV-DEFAULT -> \r\n> '
and:
    A command with a return value: 'X-SOFTWARE-VERSION x?'
    will return the echo and response: 'X-SOFTWARE-VERSION x? -> 2\r\n> '

Implements the methods to expose ARM readings as Sensors.

"""

import logging
import time

from ._base import ConsoleError
from . import tester

# Command trigger
_CMD_RUN = b'\r'
# Command suffix (between echo and response)
_CMD_SUFFIX = b' -> '
# Command prompt (after a response)
_CMD_PROMPT1 = b'\r\n> '
# Command prompt (before a response)
_CMD_PROMPT2 = '> '
# Delay between character when console echo is OFF
# NOTE: This delay is very fussy...
#       1ms will miss the T in a "TCC command about 1 in 5 test runs.
#       2ms seems to be stable.
_INTER_CHAR_DELAY = 0.002


class ConsoleGen1():

    """Communications to First Generation ARM console."""

    def __init__(self, port):
        """Initialise communications.

        @param port SimSerial port to use

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        port.timeout = 10240 / port.baudrate  # Timeout of 1kB
        self._port = port
        self._echo = True   # Character echo defaults to ON
        self._send_delay = _INTER_CHAR_DELAY
        self._read_key = None
        self.cmd_data = {}  # Data readings: Key=Name, Value=Parameter

    def open(self):
        """Open port."""
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

    def restart(self):
        """Restart ARM (It must be unlocked first)."""
        self._logger.debug('Restart')
        # We expect to see 2 banner lines after a restart
        self.action('RESTART', delay=0.5, expected=2)

    def nvwrite(self):
        """Perform NV Memory Write."""
        self._logger.debug('NV-Write')
        self.action('NV-WRITE', delay=0.5)

    def version(self):
        """Return software version."""
        verbld = self.action('SW-VERSION?', expected=1)
        self._logger.debug('Version is %s', verbld)
        return verbld

    def echo(self, echo_enable):
        """Control of console echo."""
        self._logger.debug('Echo is %s', echo_enable)
        self.action('{} ECHO'.format(int(echo_enable)))
        self._echo = echo_enable

    def send_delay(self, delay=_INTER_CHAR_DELAY):
        """Control of the delay between sent characters.

        @param delay Inter-character send delay.

        """
        self._logger.debug('Inter-char delay is %s', delay)
        self._send_delay = delay

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response line(s).

        @param command Command string.
        @param expected Expected number of responses.
        @param delay Delay between sending command and reading response.
        @return Response (a List of received line Strings).

        """
        if command:
            if self._port.simulation and self._echo:    # Auto simulate echo
                # Push echo at high priority so it is returned first
                self.puts(command, preflush=1, priority=True)
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
        if (not self._echo) and (self._send_delay == 0):
            # No echo or delay - send as a multi-byte lump
            self._port.write(cmd_data + _CMD_RUN)
        else:
            self._port.flushInput()
            # Send each byte with echo verification
            for a_byte in cmd_data:
                a_byte = bytes([a_byte])
#                self._logger.debug('Tx ---> %s', repr(a_byte))
                self._port.write(a_byte)
                if self._echo:
                    echo = self._port.read(1)
#                    self._logger.debug('Rx <--- %s', repr(echo))
                    if echo != a_byte:
                        raise ConsoleError(
                            'Command echo error. Tx: {}, Rx: {}'.format(
                                a_byte, echo))
                else:
                    time.sleep(self._send_delay)
            # And the command RUN, without echo
            self._port.write(_CMD_RUN)
#            self._logger.debug('Tx ---> %s', repr(_CMD_RUN))

    def _read_response(self, expected):
        """Read a response.

        @param expected Expected number of responses.
        @return Response (None / String / List of Strings).
        @raises ConsoleError If not enough response strings are seen.

        """
        # Read until a timeout happens
        buf = self._port.read(1024)
        if buf.startswith(_CMD_SUFFIX):
            buf = buf[len(_CMD_SUFFIX):]
        if buf.endswith(_CMD_PROMPT1):
            buf = buf[:-len(_CMD_PROMPT1)]
        if len(buf) > 0:
            response = buf.decode(errors='ignore').splitlines()
            while '' in response:
                response.remove('')
            for i in range(len(response)):
                resp = response[i]
                if resp.startswith(_CMD_PROMPT2):
                    response[i] = resp[len(_CMD_PROMPT2):]
            # Reduce a List of 1 string to just a string
            response_count = len(response)
            if response_count == 1:
                response = response[0]
        else:
            response_count = 0
            response = None
        self._logger.debug('<-- %s', repr(response))
        if response_count < expected:
            raise ConsoleError(
                'Expected {}, actual {}'.format(expected, response_count))
        return response
