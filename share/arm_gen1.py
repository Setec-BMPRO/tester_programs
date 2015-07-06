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

"""

import logging
import time

# Command trigger
_CMD_RUN = b'\r'
# Command suffix (between command echo and command response)
_CMD_SUFFIX = b' -> '
# Command prompt (after command response)
_CMD_PROMPT = b'\r\n> '


class ArmError(Exception):

    """ARM Command Echo or Response Error."""


class ArmConsoleGen1():

    """Communications to First Generation ARM console."""

    def __init__(self, serport):
        """Initialise communications.

        Set an appropriate serial read timeout.
        @param serport Opened serial port to use.

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._ser = serport
        self._ser.timeout = 10240 / self._ser.baudrate  # Timeout of 1k bytes
        self.flush()

    def flush(self):
        """Flush input (both serial port and buffer)."""
        # See what is waiting
        buf = self._ser.read(10240)
        if len(buf) > 0:
            # Show what we are flushing
            self._logger.debug('flush() %s', buf)
        self._ser.flushInput()

    def action(self, command=None, expected=0, delay=0):
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

    def _read_response(self, expected):
        """Read a response.

        @return Response (None / String / List of Strings).
        @raises ArmError If not enough response strings.

        """
        # Read until a timeout happens
        buf = self._ser.read(1024)
        # Remove leading _CMD_SUFFIX
        if buf.startswith(_CMD_SUFFIX):
            buf = buf[len(_CMD_SUFFIX):]
        # Remove trailing _CMD_PROMPT
        if buf.endswith(_CMD_PROMPT):
            buf = buf[:-len(_CMD_PROMPT)]
        if len(buf) > 0:
            response = buf.decode(errors='ignore').splitlines()
            # Reduce a List of 1 string to just a string
            response_count = len(response)
            if response_count == 1:
                response = response[0]
        else:
            response_count = 0
            response = None
        self._logger.debug('<-- %s', response)
        if response_count < expected:
            raise ArmError(
                'Expected {}, actual {}'.format(expected, response_count))
        return response

    def _write_command(self, command):
        """Write a command.

        The echo of each command character sent is read back.
        The echo of _CMD_RUN is NOT expected, or read.
        @param command Command string.
        @raises ArmError if the command does not echo.

        """
        self._logger.debug('--> %s', repr(command))
        cmd_data = command.encode()
        # Flush input to be able to read echoed characters
        self.flush()
        # Send each byte with echo verification
        for a_byte in cmd_data:
            self._ser.write(a_byte)
            echo = self._ser.read(1)
            if echo != a_byte:
                raise ArmError('Command echo error')
        # And the command RUN, without echo
        self._ser.write(_CMD_RUN)
