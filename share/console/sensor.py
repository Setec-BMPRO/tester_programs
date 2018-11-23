#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensor for Serial Consoles."""

import tester


class Sensor(tester.sensor.Sensor):

    """Console data exposed as a Sensor."""

    def __init__(self,
            console, key,
            rdgtype=tester.sensor.Reading, position=1,
            scale=1.0):
        """Create a sensor."""
        super().__init__(console, position)
        self.console = console
        self.key = key
        self._rdgtype = rdgtype
        self.scale = scale

    def configure(self):
        """Configure measurement."""
        self.console.configure(self.key)

    def read(self):
        """Take a reading.

        @return Reading

        """
        value = super().read()
        if self._rdgtype is tester.sensor.Reading:
            value = float(value) * self.scale
        rdg = self._rdgtype(value, position=self.position)
        return (rdg, )

    def __str__(self):
        """Sensor as a string.

        @return String representation of Sensor.

        """
        return 'Console: {0.doc}'.format(self)

    @property
    def doc(self):
        """Get a documentation entry, if present.

        @return Formatted doc string, or empty string

        """
        result = '({0})'.format(self.units) if self.units else ''
        result += ' {0!r}'.format(self.console.cmd_data[self.key].command)
        if self._doc:
            result += ' {0}'.format(self._doc)
        return result.strip()

    @doc.setter
    def doc(self, value):
        """Set doc property."""
        self._doc = value
