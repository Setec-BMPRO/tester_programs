#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
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

import logging
import time

import tester


class Error(Exception):

    """Console Error."""


class CommandError(Error):

    """Console Command Error."""


class ResponseError(Error):

    """Console Response Error."""


class Base:

    """Formatter for the base console. Implements Protocols 1 & 4.

    - Sends a command with '\r' on the end, in a single write.
    - Reads back the echo of the command minus the '\r'.
    - Reads response bytes, discarding '\n', until the command prompt
      '\r> ' is seen. Reading is thus done without waiting for a timeout.
    - Removes any ' -> ' string.
    - Splits the resulting string at the '\r' bytes and returns one of
      None / String / ListOfStrings.

    """

    # Command terminator. Signals the end of a command.
    cmd_terminator = b"\r"
    # Command prompt. Signals the end of response data.
    cmd_prompt = b"\r> "
    # Command suffix between echo of a command and the start of the response.
    res_suffix = b" -> "
    ignore = ()  # Tuple of strings to remove from responses
    # Fail a measurement upon a console Error
    measurement_fail_on_error = True
    # Operating as a sensor: key value
    _read_key = None
    # Data readings: Key=Name, Value=Parameter
    cmd_data = {}
    # True for verbose logging
    verbose = False
    # Time delay between port open and input flush
    open_wait_delay = 0.1
    # Response of the last call to __setitem__
    last_setitem_response = ""
    # Magic command key to read last __setitem__ response
    query_last_response = "LAST_RESPONSE?"

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self._logger = logging.getLogger(".".join((__name__, self.__class__.__name__)))
        self.port = port
        self.port.dtr = False  # BDA4 RESET not asserted
        self.port.rts = False  # BDA4 BOOT not asserted

    def __enter__(self):
        """Context Manager entry handler: Open console.

        @return self

        """
        self.open()
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler: Close console."""
        self.close()

    def open(self):
        """Open connection to unit."""
        self.port.open()
        # We need to wait just a little before flushing the port
        time.sleep(self.open_wait_delay)
        self.reset_input_buffer()

    def close(self):
        """Close connection to unit."""
        self.port.close()

    def reset_input_buffer(self):
        """Flush any waiting input."""
        self.port.reset_input_buffer()

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def opc(self):
        """Sensor: Dummy OPC.

        @return None

        """
        return None

    def read(self, callerid):  # pylint: disable=unused-argument
        """Sensor: Read ARM data using the last defined key.

        @param callerid Identity of caller
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
        return self.cmd_data[key].read(self.action)

    def __setitem__(self, key, value):
        """Write a value to the console.

        @param key Value name
        @param value Data value

        """
        self.last_setitem_response = self.cmd_data[key].write(value, self.action)

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
                self.reset_input_buffer()
                self._write_command(command)
            if delay:
                time.sleep(delay)
            reply = self._read_response(expected)
        except Error as err:
            if self.measurement_fail_on_error:
                # Read any more waiting data (a possible hard-fault message)
                port_timeout = self.port.timeout
                self.port.timeout = 0.1
                data = self.port.read(1000)
                self.port.timeout = port_timeout
                if data:
                    self._logger.error("Console Error extra data: %s", data)
                # Generate a Measurement failure
                self._logger.debug('Caught Error: "%s"', err)
                comms = tester.Measurement(
                    tester.LimitRegExp("Action", "ok", doc="Command succeeded"),
                    tester.sensor.Mirror(),
                )
                comms.sensor.store(str(err))
                comms.measure()  # Generates a test FAIL result
            else:
                raise
        return reply

    def _write_command(self, command):
        """Write a command and verify the echo.

        @param command Command string.
        @raises CommandError.

        """
        # Send the command with a terminator
        cmd_bytes = command.encode()
        self._logger.debug("Cmd --> %s", repr(cmd_bytes))
        self.port.write(cmd_bytes + self.cmd_terminator)
        # Read back the echo of the command
        cmd_echo = self.port.read(len(cmd_bytes))
        if self.verbose:
            self._logger.debug("Echo <-- %s", repr(cmd_echo))
        # The echo must match what we sent
        if cmd_echo != cmd_bytes:
            raise CommandError(
                "Command echo error. Tx: {0}, Rx: {1}".format(cmd_bytes, cmd_echo)
            )

    def _read_response(self, expected):
        """Read the response to a command.

        Discard all '\n' as they are read.
        Keep reading until a command prompt is seen.
        Remove all ignored strings.

        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises ResponseError.

        """
        # Read bytes until the command prompt is seen.
        buf = bytearray()  # Buffer for the response bytes
        while self.cmd_prompt not in buf:
            data = self.port.read(1)
            if self.verbose:
                self._logger.debug("Read <-- %s", repr(data))
            if not data:  # No data means a timeout
                raise ResponseError("Response timeout")
            if data != b"\n":  # Ignore all '\n'
                buf += data
        # Remove ignored strings
        for pattern in (self.cmd_prompt, self.res_suffix):
            buf = buf.replace(pattern, b"")
        for pattern in self.ignore:
            buf = buf.replace(pattern.encode(), b"")
        # Decode and split response lines from the byte buffer
        response = buf.decode(errors="ignore").splitlines()
        while "" in response:  # Remove empty lines
            response.remove("")
        response_count = len(response)
        if not response_count:  # Reduce empty list to None
            response = None
        elif response_count == 1:  # Reduce list of 1 string to a string
            response = response[0]
        self._logger.debug("Response <-- %s", repr(response))
        if isinstance(expected, int) and response_count != expected:
            raise ResponseError(
                "Expected {0}, actual {1}".format(expected, response_count)
            )
        return response


class BadUart(Base):

    """Formatter for the 'Bad UART' consoles. Implements Protocols 2 & 3.

    A UART that is prone to loosing characters if they arrive in a block.
    Sends a command a byte at a time with echo verification.

    """

    def _write_command(self, command):
        """Write a command and verify the echo of each byte in turn.

        @param command Command string.
        @raises CommandError.

        """
        cmd_bytes = command.encode()
        self._logger.debug("Cmd --> %s", repr(cmd_bytes))
        # Send each byte with echo verification
        index = -1
        for a_byte in cmd_bytes:
            index += 1
            a_byte = bytes([a_byte])  # We need a byte, not an integer
            self.port.write(a_byte)
            echo = self.port.read(1)
            if self.verbose:
                self._logger.debug(" Tx -> %s Rx <- %s", a_byte, echo)
            if echo != a_byte:
                raise CommandError(
                    "Command echo error on byte {0}. Tx: {1}, Rx: {2}".format(
                        index, a_byte, echo
                    )
                )
        # And the terminator without echo
        self.port.write(self.cmd_terminator)


class CANTunnel(Base):

    """Formatter for the 'CAN Tunnel' consoles. Implements Protocols 2 & 3

    - Send commands in blocks of 8-bytes maximum.
      Wait for the echo of each sent block.
      The trailing '\r' is not echoed back.
    - Response is the same as the BaseConsole class.

    """

    def _write_command(self, command):
        """Write a command and verify the echo of each block in turn.

        @param command Command string.
        @raises CommandError.

        """
        cmd_bytes = command.encode()
        self._logger.debug("Cmd --> %s", repr(cmd_bytes))
        can_packet_size = 8
        while len(cmd_bytes) > 0:
            packet = cmd_bytes[:can_packet_size]
            cmd_bytes = cmd_bytes[can_packet_size:]
            self.port.write(packet)
            echo = self.port.read(len(packet))
            if self.verbose:
                self._logger.debug(" Tx -> %s Rx <- %s", packet, echo)
            if echo != packet:
                raise CommandError(
                    "Command echo error. Tx: {0}, Rx: {1}".format(packet, echo)
                )
        # And the terminator without echo
        self.port.write(self.cmd_terminator)
