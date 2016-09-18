#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base classes for Serial Consoles."""

import logging
import tester

# Default read/write format strings (For the X-Register based consoles)
_DEF_WRITE = '{} "{} XN!'
_DEF_READ = '"{} XN?'


class Sensor(tester.sensor.Sensor):

    """Console data exposed as a Sensor."""

    def __init__(self,
            arm, key,
            rdgtype=tester.sensor.Reading, position=1,
            scale=1.0):
        """Create a sensor."""
        super().__init__(arm, position)
        self._arm = arm
        self._key = key
        self._rdgtype = rdgtype
        self._scale = scale
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
        value = super().read()
        if self._rdgtype is tester.sensor.Reading:
            value = float(value) * self._scale
        rdg = self._rdgtype(value, position=self.position)
        return (rdg, )


class ParameterError(Exception):

    """Parameter Error."""


class _Parameter():

    """Parameter base class."""

    def __init__(self, command, writeable=False, readable=True,
                       write_format=_DEF_WRITE,
                       read_format=_DEF_READ):
        """Initialise the parameter.

        @param command Command verb of this parameter.
        @param writeable True if this parameter can be written.
        @param write_format Format string for writing (value, self._cmd)
        @param read_format Format string for reading (self._cmd)

        """
        self._cmd = command
        self._writeable = writeable
        self._readable = readable
        self._wr_fmt = write_format
        self._rd_fmt = read_format

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if not self._writeable:
            raise ParameterError('Parameter is not writeable')
        write_cmd = self._wr_fmt.format(value, self._cmd)
        func(write_cmd)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Data value string.

        """
        if not self._readable:
            raise ParameterError('Parameter is not readable')
        read_cmd = self._rd_fmt.format(self._cmd)
        return func(read_cmd, expected=1)


class ParameterString(_Parameter):

    """String parameter type."""

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        super().write(value, func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return String data value.

        """
        return super().read(func)


class ParameterBoolean(_Parameter):

    """Boolean parameter type."""

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if not isinstance(value, bool):
            raise ParameterError('value "{}" must be boolean'.format(value))
        super().write(int(value), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Boolean data value.

        """
        return bool(super().read(func))


class ParameterFloat(_Parameter):

    """Float parameter type."""

    def __init__(self, command, writeable=False, readable=True,
                       minimum=0, maximum=1000, scale=1,
                       write_format=_DEF_WRITE,
                       read_format=_DEF_READ):
        """Remember the scaling and data limits."""
        super().__init__(
            command, writeable, readable, write_format, read_format)
        self._min = minimum
        self._max = maximum
        self._scale = scale

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if value < self._min or value > self._max:
            raise ParameterError(
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
        return float(value) / self._scale


class ParameterHex(_Parameter):

    """Hex parameter type with the older '$' prefix hex literal."""

    def __init__(self, command, writeable=False, readable=True,
                       minimum=0, maximum=1000, mask=0xFFFFFFFF,
                       write_format='${:08X} "{} XN!',
                       read_format='"{} XN?'):
        """Remember the data limits."""
        super().__init__(
            command, writeable, readable, write_format, read_format)
        self._min = minimum
        self._max = maximum
        self._mask = mask

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        if value < self._min or value > self._max:
            raise ParameterError(
                'Value out of range {} - {}'.format(self._min, self._max))
        super().write(int(value), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Int data value.

        """
        value = super().read(func)
        if value is None:
            value = '0'
        return int(value, 16) & self._mask


class ParameterHex0x(ParameterHex):

    """Hex parameter type with the newer '0x' prefix hex literal."""

    def __init__(self, command, writeable=False, readable=True,
                       minimum=0, maximum=1000, mask=0xFFFFFFFF):
        """Remember the data limits."""
        super().__init__(
            command, writeable, readable,
            minimum, maximum, mask, write_format='0x{:08X} "{} XN!')


class ParameterCAN(_Parameter):

    """CAN Parameter class."""

    def __init__(self, command, writeable=False):
        """Set a new read_format."""
        super().__init__(command, writeable, read_format='"{} CAN')

    def write(self, value):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        raise ParameterError('CAN parameters are read-only')

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return String value.

        """
        value = super().read(func)
        if value is None:
            value = ''
        return value


class ParameterRaw(_Parameter):

    """Raw Parameter class.

    Calls a function directly rather than generating command strings and
    using console.action().

    """

    def __init__(self, command, writeable=False, func=None):
        """Remember function to call."""
        super().__init__(command, writeable)
        self._func = func

    def write(self, value):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.

        """
        raise ParameterError('Raw parameters are read-only')

    def read(self, func):
        """Read parameter value.

        @param func Ignored.
        @return String value.

        """
        value = self._func()
        if value is None:
            value = ''
        return value
