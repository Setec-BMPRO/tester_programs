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

import tester

# Command trigger
_CMD_RUN = b'\r'
# Command suffix (between command echo and command response)
_CMD_SUFFIX = b' -> '
# Command prompt (after command response)
_CMD_PROMPT = b'\r\n> '

# Dialect dependant commands
#   Use the key name for lookup, then index by self._dialect
_DIALECT = {
    'VERSION': ('X-SOFTWARE-VERSION x?', 'SW-VERSION?'),
    'BUILD': ('X-BUILD-NUMBER x?', 'BUILD?'),
    }


class ArmError(Exception):

    """ARM Command Echo or Response Error."""


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


class ArmConsoleGen1():

    """Communications to First Generation ARM console."""

    def __init__(self, serport, dialect=0):
        """Initialise communications.

        Set an appropriate serial read timeout.
        @param serport Opened serial port to use.
        @param dialect Command dialect to use (0=SX-750,GEN8, 1=TREK2,BP35)

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._dialect = dialect
        self._ser = serport
        self._ser.timeout = 10240 / self._ser.baudrate  # Timeout of 1k bytes
        self.flush()
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, Tuple of Parameters)
        #       read_float() parameters: (Command, ScaleFactor, StrKill)
        self._data = {
#            'ARM-AcDuty': (self.read_float,
#                            ('X-AC-DETECTOR-DUTY X?', 1, '%')),
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

    def read_float(self, data):
        """Get float value from ARM.

        @return Value

        """
        cmd, scale, strkill = data
        reply = self.action(cmd, expected=1)
# FIXME: There has to be a better way than this...
        if reply is None:
            value = -999.999
        else:
            reply = reply.replace(strkill, '')
            value = float(reply) * scale
        return value

    def defaults(self):
        """Write factory defaults into NV memory."""
        self._logger.debug('Write factory defaults')
        self.unlock()
        self.action('NV-DEFAULT')
        self.nvwrite()
        # We expect to see 2 banner lines after a restart
        self.action('RESTART', delay=0.5, expected=2)

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
        ver_cmd = _DIALECT['VERSION'][self._dialect]
        bld_cmd = _DIALECT['BUILD'][self._dialect]
        ver = self.action(ver_cmd, expected=1)
        bld = self.action(bld_cmd, expected=1)
        verbld = '.'.join((ver, bld))
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

    def _read_response(self, expected):
        """Read a response.

        @param expected Expected number of responses.
        @return Response (None / String / List of Strings).
        @raises ArmError If not enough response strings are seen.

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
            # Remove any empty strings
            while '' in response:
                response.remove('')
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
            a_byte = bytes([a_byte])
            self._ser.write(a_byte)
            echo = self._ser.read(1)
            if echo != a_byte:
                raise ArmError(
                    'Command echo error. Sent {}, Rx {}'.format(a_byte, echo))
        # And the command RUN, without echo
        self._ser.write(_CMD_RUN)

    def flush(self):
        """Flush input (both serial port and buffer)."""
        # See what is waiting
        buf = self._ser.read(10240)
        if len(buf) > 0:
            # Show what we are flushing
            self._logger.debug('flush() %s', buf)
        self._ser.flushInput()
