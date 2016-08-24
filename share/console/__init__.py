#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serial Console Drivers."""

# Easy access to utility methods and classes
from ._base import *
from .protocol import *
import tester
import testlimit

# Result values to store into the mirror sensors
_SUCCESS = 0
_FAILURE = 1


class Variable():

    """Console variable reader-writer processor."""

    def __init__(self):
        """Initialise."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._read_key = None
        self.cmd_data = {}  # Data readings: Key=Name, Value=Parameter
        limit = testlimit.LimitHiLo(
            'Comms', 0, (_SUCCESS - 0.5, _SUCCESS + 0.5))
        self._comms = tester.Measurement(limit, sensor.Mirror())

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
        except ConsoleError as err:
            self._logger.debug('Caught ConsoleError %s', err)
            self._comms.sensor.store(_FAILURE)
            self._comms.measure()   # Generates a test FAIL result
        return reply

    def __setitem__(self, key, value):
        """Write a value to the console.

        @param key Value name
        @param value Data value

        """
        try:
            parameter = self.cmd_data[key]
            parameter.write(value, self.action)
        except ConsoleError as err:
            self._logger.debug('Caught ConsoleError %s', err)
            self._comms.sensor.store(_FAILURE)
            self._comms.measure()   # Generates a test FAIL result
