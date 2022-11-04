#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""Parameters for Serial Consoles."""

import enum


class ParameterError(Exception):

    """Parameter Error."""


class _Parameter:

    """Parameter base class."""

    # Default read/write format strings for the X-Register based consoles
    _wr_fmt = '{0} "{1} XN!'
    _rd_fmt = '"{0} XN?'

    def __init__(
        self,
        command,
        writeable=False,
        readable=True,
        write_format=None,
        read_format=None,
        write_expected=0,
        read_expected=1,
    ):
        """Initialise the parameter.

        @param command Command verb of this parameter.
        @param writeable True if this parameter can be written.
        @param readable True if this parameter can be read.
        @param write_format Format string for writing
        @param read_format Format string for reading
        @param write_expected Expected response lines for a write
        @param read_expected Expected response lines for a read

        """
        self.command = command
        self._writeable = writeable
        self._readable = readable
        if write_format:
            self._wr_fmt = write_format
        if read_format:
            self._rd_fmt = read_format
        self.write_expected = write_expected
        self.read_expected = read_expected

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.
        @return Command response.

        """
        if not self._writeable:
            raise ParameterError("Parameter is not writable")
        write_cmd = self._wr_fmt.format(value, self.command)
        response = func(write_cmd, expected=self.write_expected)
        return response

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Command response.

        """
        if not self._readable:
            raise ParameterError("Parameter is not readable")
        read_cmd = self._rd_fmt.format(self.command)
        response = func(read_cmd, expected=self.read_expected)
        return response


class String(_Parameter):

    """String parameter type."""


class Boolean(_Parameter):

    """Boolean parameter type."""

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.
        @return Command response

        """
        if not isinstance(value, bool):
            raise ParameterError('value "{0}" must be boolean'.format(value))
        return super().write(int(value), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Boolean data value.

        """
        return bool(int(super().read(func).strip()))


class Float(_Parameter):

    """Float parameter type."""

    def __init__(
        self,
        command,
        writeable=False,
        readable=True,
        minimum=0,
        maximum=1000,
        scale=1,
        write_format=None,
        read_format=None,
        write_expected=0,
        read_expected=1,
    ):
        """Remember the scaling and data limits."""
        super().__init__(
            command,
            writeable,
            readable,
            write_format,
            read_format,
            write_expected,
            read_expected,
        )
        self.min = minimum
        self.max = maximum
        self.scale = scale

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.
        @return Command response

        """
        if value < self.min or value > self.max:
            raise ParameterError(
                "Value out of range {0} → {1}".format(self.min, self.max)
            )
        return super().write(round(value * self.scale), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Float data value.

        """
        value = super().read(func)
        if value is None:
            value = "0"
        return float(value) / self.scale


class Calibration(Float):

    """A write-only parameter for calibration commands."""

    # write format string
    _wr_fmt = '{0} "{1} CAL'

    def __init__(self, command, scale=1000, write_expected=1):
        """Override write_format and create instance."""
        super().__init__(
            command, writeable=True, scale=scale, write_expected=write_expected
        )


class Hex(_Parameter):

    """Hex parameter type with '$' prefix hex literal."""

    # write format string
    _wr_fmt = '${0:08X} "{1} XN!'

    def __init__(
        self,
        command,
        writeable=False,
        readable=True,
        minimum=0,
        maximum=1000,
        scale=1,
        mask=0xFFFFFFFF,
        write_format=None,
        read_format=None,
        write_expected=0,
        read_expected=1,
    ):
        """Remember the data limits."""
        super().__init__(
            command,
            writeable,
            readable,
            write_format,
            read_format,
            write_expected,
            read_expected,
        )
        self.min = minimum
        self.max = maximum
        self.scale = scale
        self.mask = mask

    def write(self, value, func):
        """Write parameter value.

        @param value Data value.
        @param func Function to use to write the value.
        @return Command response

        """
        if value < self.min or value > self.max:
            raise ParameterError(
                "Value out of range {0} → {1}".format(self.min, self.max)
            )
        return super().write(round(value * self.scale), func)

    def read(self, func):
        """Read parameter value.

        @param func Function to use to read the value.
        @return Int data value.

        """
        value = super().read(func)
        if value is None:
            value = "0"
        return (int(value, 16) & self.mask) / self.scale


@enum.unique
class OverrideTo(enum.IntEnum):

    """Console manual override constants."""

    NORMAL = 0
    FORCE_OFF = 1
    FORCE_ON = 2


class Override(Float):

    """A parameter for overriding SamB11 unit operation."""

    def __init__(self, command):
        """Create instance."""
        super().__init__(
            command, writeable=True, minimum=min(OverrideTo), maximum=max(OverrideTo)
        )
