#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Arduino console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Arduino(console.Variable, console.BaseConsole):

    """Communications to SX-750 Arduino console."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)
        self.cmd_data = {
            'VERSION': ParameterString(
                'VERSION?', read_format='{}'),
            'DEBUG': ParameterString(
                '1 DEBUG', read_format='{}'),
            'QUIET': ParameterString(
                '0 DEBUG', read_format='{}'),
            'PGM_5VSB': ParameterString(
                'PROGRAM-5VSB', read_format='{}'),
            'PGM_PWRSW': ParameterString(
                'PROGRAM-PWRSW', read_format='{}'),
            'POT_MIN': ParameterString(
                'POT-MIN', read_format='{}'),
            '12_POT_ENABLE': ParameterString(
                '12 POT-ENABLE', read_format='{}'),
            '24_POT_ENABLE': ParameterString(
                '24 POT-ENABLE', read_format='{}'),
            'POT_STEP': ParameterString(
                'POT-STEP', read_format='{}'),
            'POT_DISABLE': ParameterString(
                'POT-DISABLE', read_format='{}'),
            }
