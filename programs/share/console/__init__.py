#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serial Console Drivers."""


# Easy access to utility methods and classes
from ._base import *
from .protocol import *
from .arm_gen1 import *
from .arm_gen2 import *
import tester


class Variable():

    """Console variable reader-writer processor."""

    def __init__(self, *args, **kwargs):
        """Initialise."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._read_key = None
        self.cmd_data = {}  # Data readings: Key=Name, Value=Parameter
        super().__init__(*args, **kwargs)

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
            raise tester.measure.MeasurementFailedError
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
            raise tester.measure.MeasurementFailedError
