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

from share.sim_serial import SimSerial
import tester

# Command trigger
_CMD_RUN = b'\r'
# Command suffix (between echo and response)
_CMD_SUFFIX = b' -> '
# Command prompt (after a response)
_CMD_PROMPT1 = b'\r\n> '
# Command prompt (before a response)
_CMD_PROMPT2 = '> '
# Delay after a value set command
_SET_DELAY = 0.3

# Dialect dependent commands
#   Use the key name for lookup, then index by self._dialect
# Dialect 0 = SX-750, GEN8
# Dialect 1 = BatteryCheck, BP35, Trek2
_DIALECT = {
    'VERSION': ('X-SOFTWARE-VERSION x?', 'SW-VERSION?'),
    'BUILD': ('X-BUILD-NUMBER x?', 'BUILD?'),
    }
# Dialect dependent features
#   Dialect 1 has the 'SET-HW-VER' and 'SET-SERIAL-ID' commands.
#   BatteryCheck has the 'SET-SERIAL-ID' command, but it works differently
#   to the Dialect 1 units...


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


class _Parameter():

    """Parameter base class."""

    def __init__(self, command, writeable=False):
        """Remember the command verb and writeable state."""
        self._cmd = command
        self._writeable = writeable

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if not self._writeable:
            raise ValueError('Parameter is read-only')
        write_cmd = '{} "{} XN!'.format(value, self._cmd)
        func(write_cmd, delay=_SET_DELAY)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Data value.

        """
        read_cmd = '"{} XN?'.format(self._cmd)
        return func(read_cmd, expected=1)


class ParameterBoolean(_Parameter):

    """Boolean parameter type."""

    error_value = False

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if not isinstance(value, bool):
            raise ValueError('value "{}" must be boolean'.format(value))
        super().write(int(value), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Boolean data value.

        """
        return bool(super().read(func))


class ParameterFloat(_Parameter):

    """Float parameter type."""

    error_value = float('NaN')

    def __init__(self, command, writeable=False,
                       minimum=0, maximum=1000, scale=1):
        """Remember the scaling and data limits."""
        super().__init__(command, writeable)
        self._min = minimum
        self._max = maximum
        self._scale = scale

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if value < self._min or value > self._max:
            raise ValueError(
                'Value out of range {} - {}'.format(self._min, self._max))
        super().write(int(value * self._scale), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Float data value.

        """
        value = super().read(func)
        if value is None:
            value = '0'
        return int(value) / self._scale


class ParameterHex(_Parameter):

    """Hex parameter type."""

    error_value = float('NaN')

    def __init__(self, command, writeable=False,
                 minimum=0, maximum=1000, mask=0xFFFFFFFF):
        """Remember the data limits."""
        super().__init__(command, writeable)
        self._min = minimum
        self._max = maximum
        self._mask = mask

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if value < self._min or value > self._max:
            raise ValueError(
                'Value out of range {} - {}'.format(self._min, self._max))
        if not self._writeable:
            raise ValueError('Parameter is read-only')
        write_cmd = '${:08X} "{} XN!'.format(value, self._cmd)
        func(write_cmd, delay=_SET_DELAY)

    def read(self, func):
        """Read parameter value.

        @param value String value from the unit, or None.
        @return Int data value.

        """
        value = super().read(func)
        if value is None:
            value = '0'
        return int(value, 16) & self._mask


class ParameterCAN(_Parameter):

    """CAN Parameter class."""

    error_value = ''

    def write(self, value):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        raise ValueError('CAN parameters are read-only')

    def read(self, func):
        """Read parameter value.

        @param func Function to use to write the value.
        @return String value.

        """
        can_cmd = '"{} CAN'.format(self._cmd)
        value = func(can_cmd, expected=1)
        if value is None:
            value = ''
        return value


class ParameterRaw(_Parameter):

    """Raw Parameter class.

    Calls a function directly rather than generating command strings and
    using console.action().

    """

    error_value = ''

    def __init__(self, command, writeable=False, func=None):
        """Remember function to call."""
        super().__init__(command, writeable)
        self._func = func

    def write(self, value):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        raise ValueError('Raw parameters are read-only')

    def read(self, func):
        """Read parameter value.

        @param func Ignored.
        @return String value.

        """
        value = self._func()
        if value is None:
            value = ''
        return value


class ArmConsoleGen1(SimSerial):

    """Communications to First Generation ARM console."""

    def __init__(self, dialect=0, simulation=False, **kwargs):
        """Initialise communications.

        @param dialect Command dialect to use (0=SX-750,GEN8, 1=TREK2,BP35)

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._dialect = dialect
        self._can_tunnel = False        # CAN tunneling OFF
        self._read_key = None
        # Data readings: Key=Name, Value=Parameter
        self.cmd_data = {}
        # Initialise the SimSerial()
        super().__init__(simulation=simulation, **kwargs)

    def close(self):
        """Close, and ignore any errors."""
        try:
            super().close()
        except:
            pass

    def setPort(self, port):
        """Set serial port.

        @param port Serial port to use.
        Set an appropriate serial read timeout.

        """
        self._logger.debug('Set port: %s', port)
        self.timeout = 10240 / self.baudrate  # Timeout of 1kB
        super().setPort(port)

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
        except ArmError:
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
        except ArmError:
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
        if self._dialect != 0:
            self.action('{0[0]} {0[1]} "{0[2]} SET-HW-VER'.format(hwver))
            self.action('"{} SET-SERIAL-ID'.format(sernum))
        self.action('NV-DEFAULT')
        self.nvwrite()

    def unlock(self):
        """Unlock the ARM."""
        self._logger.debug('Unlock')
        self.action('$DEADBEA7 UNLOCK')

    def restart(self):
        """Restart ARM (It must be unlocked)."""
        self._logger.debug('Restart')
        # We expect to see 2 banner lines after a restart
        self.action('RESTART', delay=0.5, expected=2)

    def nvwrite(self):
        """Perform NV Memory Write."""
        self._logger.debug('NV-Write')
        self.action('NV-WRITE', delay=0.5)

    def version(self):
        """Return software version."""
        if self._dialect == 0:
            ver_cmd = _DIALECT['VERSION'][self._dialect]
            bld_cmd = _DIALECT['BUILD'][self._dialect]
            ver = self.action(ver_cmd, expected=1)
            bld = self.action(bld_cmd, expected=1)
            verbld = '.'.join((ver, bld))
        else:
            ver_cmd = _DIALECT['VERSION'][self._dialect]
            verbld = self.action(ver_cmd, expected=1)
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
            if self.simulation:     # Auto simulate the command echo
                postflush = 0 if expected > 0 else 1
                # Push echo at high priority so it is returned first
                self.putch(
                    command, preflush=1, postflush=postflush, priority=True)
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected)

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
            self._write(a_byte)
            echo = self._read(1)
            if echo != a_byte:
                raise ArmError(
                    'Command echo error. Tx: {}, Rx: {}'.format(a_byte, echo))
        # And the command RUN, without echo
        self._write(_CMD_RUN)

    def _read_response(self, expected):
        """Read a response.

        @param expected Expected number of responses.
        @return Response (None / String / List of Strings).
        @raises ArmError If not enough response strings are seen.

        """
        # Read until a timeout happens
        buf = self._read(1024)
#        self._logger.debug('<== %s', buf)
        # Remove leading _CMD_SUFFIX
        if buf.startswith(_CMD_SUFFIX):
            buf = buf[len(_CMD_SUFFIX):]
        # Remove trailing _CMD_PROMPT
        if buf.endswith(_CMD_PROMPT1):
            buf = buf[:-len(_CMD_PROMPT1)]
        if len(buf) > 0:
            response = buf.decode(errors='ignore').splitlines()
            # Remove any empty strings
            while '' in response:
                response.remove('')
            # Trim any leading command prompts
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
            raise ArmError(
                'Expected {}, actual {}'.format(expected, response_count))
        return response

    def flush(self):
        """Flush input by reading everything."""
        # See what is waiting
        buf = self._read(1024 * 1024)
        if len(buf) > 0:
            # Show what we are flushing
            self._logger.debug('flush() %s', buf)

    def ct_open(self, target_id):
        """Open a CAN tunnel.

        The console of the target device will be presented as if it where
        the console of this instance.

        @param target_id CAN ID of the target device."""
# TODO: Open the CAN tunnel
        self._can_tunnel = True

    def ct_close(self):
        """Close a CAN tunnel."""
# TODO: Close the CAN tunnel
        self._can_tunnel = False

    def _read(self, size=1):
        """Read characters from CAN tunnel or serial."""
        if not self._can_tunnel:
            return super().read(size)
# TODO: Read the CAN tunnel

    def _write(self, data):
        """Write characters to CAN tunnel or serial."""
        if not self._can_tunnel:
            super().write(data)
# TODO: Write to the CAN tunnel
