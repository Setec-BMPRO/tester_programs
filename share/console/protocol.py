#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console driver Command-Response protocol processor.

Filter layer between the Serial port that implements the Command/Response
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
import tester



class Error(Exception):

    """Console Error."""


class CommandError(Error):

    """Console Command Error."""


class ResponseError(Error):

    """Console Response Error."""


class Base():

    """Formatter for the base console. Implements Protocols 1 & 4.

    - Sends a command with '\r' on the end, in a single write.
    - Reads back the echo of the command minus the '\r'.
    - Reads response bytes, discarding '\n', until the command prompt
      '\r> ' is seen. Reading is thus done without waiting for a timeout.
    - Removes any ' -> ' string.
    - Splits the resulting string at the '\r' bytes and returns one of
      None / String / ListOfStrings.

    """

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b'\r> '
    # Command suffix between echo of a command and the start of the response.
    res_suffix = b' -> '
    ignore = ()    # Tuple of strings to remove from responses
    # Fail a measurement upon a console Error
    measurement_fail_on_error = True
    # Operating as a sensor: key value
    _read_key = None
    # Data readings: Key=Name, Value=Parameter
    cmd_data = {}
    # True for verbose logging
    verbose = False
# TODO: Remove this logger once we implement response_count != expected
    # Last command sent (for debug message @ line 248)
    last_cmd = None
    # Response of the last call to __setitem__
    last_setitem_response = ''
    # Magic command key to read last __setitem__ response
    query_last_response = 'LAST_RESPONSE?'

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.port = port
        self.open = port.open
        self.close = port.close
        self.opc = lambda: None         # Sensor: Dummy OPC

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def read(self):
        """Sensor: Read ARM data using the last defined key.

        @return Value

        """
        return self[self._read_key]

    def __getitem__(self, key):
        """Read a value from the console.

        @param key Value name
        @return Reading

        """
        if key == self.query_last_response:
            return self.last_setitem_response
        else:
            return self.cmd_data[key].read(self.action)

    def __setitem__(self, key, value):
        """Write a value to the console.

        @param key Value name
        @param value Data value

        """
        self.last_setitem_response = (
            self.cmd_data[key].write(value, self.action))

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response.

        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises Error.

        """
        reply = None
        try:
            if command:
                self.last_cmd = command
                self.port.flushInput()
                self._write_command(command)
            if delay:
                time.sleep(delay)
            reply = self._read_response(expected)
        except Error as err:
            if self.measurement_fail_on_error:
                self._logger.debug('Caught Error: "%s"', err)
                comms = tester.Measurement(
                    tester.LimitInteger('Action', 0, doc='Command succeeded'),
                    tester.sensor.Mirror())
                comms.sensor.store(1)
                comms.measure()   # Generates a test FAIL result
            else:
                raise
        return reply

    def _write_command(self, command):
        """Write a command and verify the echo.

        @param command Command string.
        @raises CommandError.

        """
        # Send the command with a '\r'
        cmd_bytes = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_bytes))
        self.port.write(cmd_bytes + b'\r')
        # Read back the echo of the command
        cmd_echo = self.port.read(len(cmd_bytes))
        if self.verbose:
            self._logger.debug('Echo <-- %s', repr(cmd_echo))
        # The echo must match what we sent
        if cmd_echo != cmd_bytes:
            raise CommandError('Command echo error')

    def _read_response(self, expected):
        """Read the response to a command.

        Discard all '\n' as they are read. Keep reading until a command
        prompt ('\r> ') is seen.

        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises ResponseError.

        """
        # Read bytes until the command prompt is seen.
        buf = bytearray()           # Buffer for the response bytes
        while self.cmd_prompt not in buf:
            data = self.port.read(1)
            if self.verbose:
                self._logger.debug('Read <-- %s', repr(data))
            if len(data) == 0:              # No data means a timeout
                raise ResponseError('Response timeout')
            buf += data
            buf = buf.replace(b'\n', b'')   # Remove all '\n'
        buf = buf.replace(self.cmd_prompt, b'') # Remove the command prompt
        buf = buf.replace(self.res_suffix, b'') # Remove any ' -> '
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
# FIXME: Next line should be:   if response_count != expected:
        if response_count < expected:
            raise ResponseError(
                'Expected {0}, actual {1}'.format(expected, response_count))
# TODO: Remove this logger once we implement response_count != expected
        if response_count > expected:
            self._logger.error(
                'Extra response to %s: Expected %s, actual %s',
                repr(self.last_cmd), expected, repr(response))
        return response


class BadUart(Base):

    """Formatter for the 'Bad UART' consoles. Implements Protocols 2 & 3

    - Sends a command with '\r' on the end, a byte at a time with echo
      verification. The trailing '\r' is not echoed back.
    - Response is the same as the BaseConsole class.

    """

    def _write_command(self, command):
        """Write a command and verify the echo of each byte in turn.

        @param command Command string.
        @raises CommandError.

        """
        cmd_bytes = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_bytes))
        # Send each byte with echo verification
        for a_byte in cmd_bytes:
            a_byte = bytes([a_byte])    # We need a byte, not an integer
            self.port.write(a_byte)
            echo = self.port.read(1)
            if self.verbose:
                self._logger.debug(' Tx -> %s Rx <- %s', a_byte, echo)
            if echo != a_byte:
                raise CommandError(
                    'Command echo error. Tx: {0}, Rx: {1}'.format(
                        a_byte, echo))
        # And the '\r' without echo
        self.port.write(b'\r')


class CANTunnel(Base):

    """Formatter for the 'CAN Tunnel' consoles. Implements Protocols 2 & 3

    - Allow for possible CAN packet loss by send commands in blocks of
      8-bytes maximum. Wait for the echo of each sent block.
      The trailing '\r' is not echoed back.
    - Response is the same as the BaseConsole class.

    """

    def _write_command(self, command):
        """Write a command and verify the echo of each block in turn.

        @param command Command string.
        @raises CommandError.

        """
        cmd_bytes = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_bytes))
        can_packet_size = 8
        while len(cmd_bytes) > 0:
            packet = cmd_bytes[:can_packet_size]
            cmd_bytes = cmd_bytes[can_packet_size:]
            self.port.write(packet)
            echo = self.port.read(len(packet))
            if self.verbose:
                self._logger.debug(' Tx -> %s Rx <- %s', packet, echo)
            if echo != packet:
                raise CommandError(
                    'Command echo error. Tx: {0}, Rx: {1}'.format(
                        packet, echo))
        # And the '\r' without echo
        self.port.write(b'\r')
