#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""Base class for Programmers."""

import abc

import libtester
import tester


class _Base(abc.ABC):
    """Programmer base class."""

    pass_result = r"ok"

    def __init__(self):
        """Create a programmer."""
        self._measurement = tester.Measurement(
            libtester.LimitRegExp("Program", self.pass_result, "Programming succeeded"),
            tester.sensor.Mirror(),
        )
        self._result = None

    @property
    def result(self):
        """Programming result value.

        @return Result value

        """
        return self._result

    @result.setter
    def result(self, value):
        """Set programming result.

        @param value Result

        """
        if not isinstance(value, str):  # A subprocess exit code
            if value:
                value = "Error {0}".format(value)
            else:
                value = self.pass_result
        self._result = value
        self._measurement.sensor.store(self._result)

    def result_check(self):
        """Check the programming result."""
        self._measurement()

    @property
    def position(self):
        """Position property of the internal mirror sensor.

        @return Position information

        """
        return self._measurement.sensor.position

    @position.setter
    def position(self, value):
        """Set internal mirror sensor position property.

        @param value Position value or Tuple(values)

        """
        self._measurement.sensor.position = value

    def program(self):
        """Program a device and return when finished."""
        self.program_begin()
        self.program_wait()

    @abc.abstractmethod
    def program_begin(self):
        """Begin device programming."""

    @abc.abstractmethod
    def program_wait(self):
        """Wait for device programming to finish."""


class VerificationError(Exception):
    """Verification error."""
