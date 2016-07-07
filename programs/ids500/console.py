#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 PIC processor console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Console(console.Variable, console.BaseConsole):

    """Communications to Drifter console."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)
        self.cmd_data = {
            'PIC-SwRev': ParameterString(
                '?,I,1', read_format='{}'),
            'PIC-MicroTemp': ParameterString(
                '?,D,16', read_format='{}'),
            }
