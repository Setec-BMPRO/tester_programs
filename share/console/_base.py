#!/usr/bin/env python3
"""Base classes for Serial Consoles."""

import logging

import tester


# Delay after a value set command
_SET_DELAY = 0.3


class ConsoleError(Exception):

    """Serial Command Echo or Response Error."""


class Sensor(tester.sensor.Sensor):

    """Console data exposed as a Sensor."""

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
        """Initialise the parameter.

        @param command Command verb of this parameter.
        @param writeable True if this parameter can be written.

        """
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
        @return Data value string.

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
# FIXME: Deal with the '$' vs '0x' options
        write_cmd = '${:08X} "{} XN!'.format(value, self._cmd)
        func(write_cmd, delay=_SET_DELAY)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
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

        @param func Function to use to read the value.
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
