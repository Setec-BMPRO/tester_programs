#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serial Console Drivers."""

# Easy access to utility methods and classes
from ._base import *
from .protocol import *
import tester


class Variable():

    """Console variable reader-writer processor."""

    _read_key = None
    cmd_data = {}  # Data readings: Key=Name, Value=Parameter

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
        parameter = self.cmd_data[key]
        return parameter.read(self.action)

    def __setitem__(self, key, value):
        """Write a value to the console.

        @param key Value name
        @param value Data value

        """
        parameter = self.cmd_data[key]
        parameter.write(value, self.action)
