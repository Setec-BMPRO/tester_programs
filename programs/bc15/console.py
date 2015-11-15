#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 ARM processor console driver."""

from ..share import console


Sensor = console.Sensor

# Some easier to use short names
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex
ParameterRaw = console.ParameterRaw


class Console(console.ConsoleGen2):

    """Communications to BC15 console."""

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        self.cmd_data = {
            'SwVer': ParameterRaw('', func=self.version),
            }

    def ps_mode(self):
        """Set the unit into Power Supply mode."""
        self.action('0 MAINLOOP')
        self.action('STOP')
        self.action('15000 SETMA')
        self.action('14400 SETMV')
        self.action('0 0 PULSE')
        self.action('RESETOVERVOLT')
        self.action('1 SETDCDCEN')
        self.action('1 SETPSON')
        self.action('1 SETDCDCOUT')
        self.action('0 SETPSON', delay=0.5)
