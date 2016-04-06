#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console driver Command-Response protocol processor.

Filter layer between the SimSerial port that implements the Command/Response
protocol of the console.
Several versions of console 'languages' exist, that each use different syntax.

Protocol 1: SX-750, GEN8 [ LPC111x CPU, No RTOS ]
    The UART is implemented in hardware and has buffering.

    Commands are terminated with '\r' and written in a single write.
    The trailing '\r' is not echoed back.

    Responses end with '\r' only. '\n' is never sent from the unit.
    In 'user' mode (echo is ON):
      Responses are preceded by ' -> ', and there is a final command prompt
      of '> '.
      A command 'Q?' with response '123' is received as 'Q? -> 123\r> '.
    In 'host' mode (echo is OFF):
      The prefix and prompt are not sent.
      A command 'Q?' with response '123' is received as '123\r'.

Protocol 2: BatteryCheck [ LPC1519 CPU, No RTOS, Software serial port ]
    The UART is implemented in software and is prone to loosing bytes.

    Commands are terminated with '\r' and written a byte at a time with a wait
    for the echo of the byte before sending the next byte. The trailing '\r'
    is not echoed back. Due to the UART problems, echo must be left ON.

    Responses end with '\r' only. '\n' is never sent from the unit.
    Responses are preceded by ' -> ', and there is a final command prompt
    of '> '.
    A command 'Q?' with response '123' is received as 'Q? -> 123\r> '.

Protocol 3: BP35, CN101, Trek2 [ LPC1519 CPU, RTOS, CPU UART ]
    The UART is implemented in hardware but has no buffering, and the RTOS
    disables interrupts for longer than a character time (100-200us).
    Thus the UART can loose incoming bytes.

    Commands are terminated with '\r' and written a byte at a time with a wait
    for the echo of the byte before sending the next byte. The trailing '\r'
    is not echoed back. Due to the UART problems, echo must be left ON.

    Responses lines end with '\r\n', but the prompt does not.
    Responses are preceded by ' -> ', and there is a final command prompt
    of '> '.
    A command 'Q?' with response '123' is received as 'Q? -> 123\r\n> '.

Protocol 4: BC15 [ LPC111x CPU, No RTOS ]
    The UART is implemented in hardware and has buffering.

    Commands are terminated with '\r' and written in a single write.
    The trailing '\r' is not echoed back.

    Responses lines end with '\r\n', and there is a final command prompt
    of '> '. The command prompt can be changed to include '\n'.
    A command 'Q?' with response '123' is received as 'Q?123\r\n> '.

"""

import time
import logging

# Console command prompt. Signals the end of output data.
_CMD_PROMPT = b'\r> '
# Command suffix between echo of a command and the response.
_RES_SUFFIX = b' -> '


class ConsoleError(Exception):

    """Console Error."""


class ConsoleCommandError(ConsoleError):

    """Console Command Error."""


class ConsoleResponseError(ConsoleError):

    """Console Response Error."""


class BaseConsole():

    """Formatter for the base console. Implements Protocols 1 & 4.

    - Sends a command with '\r' on the end, in a single write.
    - Reads back the echo of the command minus the '\r'.
    - Reads response bytes, discarding '\n', until the command prompt
      '\r> ' is seen. Reading is thus done without waiting for a timeout.
    - Removes any ' -> ' string.
    - Splits the resulting string at the '\r' bytes and returns one of
      None / String / ListOfStrings.

    """

    def __init__(self, port, timeout=2.0, verbose=False):
        """Initialise communications.

        @param port SimSerial instance to use
        @param timeout Serial port timeout in sec

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._port = port
        self._port.timeout = timeout
        self.ignore = ()    # Tuple of strings to remove from responses
        self._verbose = verbose

    def open(self):
        """Open port."""
        self._port.open()

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Put a string into the read-back buffer.

        @param string_data Data string, or tuple of data strings.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to put in front of the buffer.

        """
        self._port.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Close serial communications."""
        self._port.close()

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response.

        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises ConsoleError.

        """
        if command:
            if self._port.simulation:   # Auto simulate the command echo
                self._port.puts(command, preflush=1, priority=True)
            self._port.flushInput()
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected)

    def _write_command(self, command):
        """Write a command and verify the echo.

        @param command Command string.
        @raises ConsoleCommandError.

        """
        # Send the command with a '\r'
        cmd_data = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_data))
        self._port.write(cmd_data + b'\r')
        # Read back the echo of the command
        cmd_echo = self._port.read(len(cmd_data))
        if self._verbose:
            self._logger.debug('Echo <-- %s', repr(cmd_echo))
        # The echo must match what we sent
        if cmd_echo != cmd_data:
            raise ConsoleCommandError('Command echo error')

    def _read_response(self, expected):
        """Read the response to a command.

        Discard all '\n' as they are read. Keep reading until a command
        prompt ('\r> ') is seen.

        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises ConsoleResponseError.

        """
        # Read bytes until the command prompt is seen.
        buf = bytearray()           # Buffer for the response bytes
        while _CMD_PROMPT not in buf:
# TODO: Maybe we can read more than 1 byte at a time...?
#   Doing so makes it hard to use the SimSerial simulation, since this
#   console does NOT call flushInput(), so the flush markers cannot be used to
#   limit the inWaiting() response.
            data = self._port.read(1)
            if self._verbose:
                self._logger.debug('Read <-- %s', repr(data))
            if len(data) == 0:              # No data means a timeout
                raise ConsoleResponseError('Response timeout')
            buf += data
            buf = buf.replace(b'\n', b'')   # Remove all '\n'
        buf = buf.replace(_CMD_PROMPT, b'') # Remove the command prompt
        buf = buf.replace(_RES_SUFFIX, b'') # Remove any ' -> '
        for pattern in self.ignore:         # Remove ignored strings
            buf = buf.replace(pattern.encode(), b'')
        # Decode and split response lines from the byte buffer
        response = buf.decode(errors='ignore').splitlines()
        while '' in response:       # Remove empty lines
            response.remove('')
        response_count = len(response)
        if response_count == 1:     # Reduce list of 1 string to a string
            response = response[0]
        if response_count == 0:     # Reduce empty list to None
            response = None
        self._logger.debug('Response <-- %s', repr(response))
        if response_count < expected:
            raise ConsoleResponseError(
                'Expected {}, actual {}'.format(expected, response_count))
        return response


class BadUartConsole(BaseConsole):

    """Formatter for the 'Bad UART' consoles. Implements Protocols 2 & 3

    - Sends a command with '\r' on the end, a byte at a time with echo
      verification. The trailing '\r' is not echoed back.
    - Response is the same as the BaseConsole class.

    """

    def _write_command(self, command):
        """Write a command and verify the echo of each byte in turn.

        @param command Command string.
        @raises ConsoleCommandError.

        """
        cmd_data = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_data))
        # Send each byte with echo verification
        for a_byte in cmd_data:
            a_byte = bytes([a_byte])    # We need a byte, not an integer
            self._port.write(a_byte)
            echo = self._port.read(1)
            if self._verbose:
                self._logger.debug(' Tx -> %s Rx <- %s', a_byte, echo)
            if echo != a_byte:
                raise ConsoleCommandError(
                    'Command echo error. Tx: {}, Rx: {}'.format(
                        a_byte, echo))
        # And the '\r' without echo
        self._port.write(b'\r')
