#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serial Console Drivers."""


# Easy access to utility methods and classes
from ._base import *
from ._protocol import *
from .arm_gen0 import *
from .arm_gen1 import *
from .arm_gen2 import *
import tester


class Variable():

    """Console variable processor."""

    def __init__(self):
        """Initialise."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._read_key = None
        self.cmd_data = {}  # Data readings: Key=Name, Value=Parameter

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
        """Read a value from the console.

        @param key Value name
        @return Reading

        """
        try:
            parameter = self.cmd_data[key]
            reply = parameter.read(self.action)
# FIXME:
#   If we raise a ConsoleError here, the test result will be SYSTEM ERROR
#   instead of a FAIL. Return an 'error' reading value to get a test FAIL.
#   There must be a cleaner way to do this using exceptions...
        except ConsoleError:
            # Sensor uses this, so we must always return a valid reading
            reply = parameter.error_value
        return reply

    def __setitem__(self, key, value):
        """Write a value to the console.

        @param key Value name
        @param value Data value

        """
        try:
            parameter = self.cmd_data[key]
            parameter.write(value, self.action)
# FIXME:
#   If we raise a ConsoleError here, the test result will be SYSTEM ERROR
#   instead of a FAIL.
#   This exception will make the unit FAIL the test.
        except ConsoleError:
            raise tester.measure.MeasurementFailedError
