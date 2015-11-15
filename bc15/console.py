#!/usr/bin/env python3
"""BC15 ARM processor console driver."""

import share.console


Sensor = share.console.Sensor

# Some easier to use short names
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat
ParameterHex = share.console.ParameterHex
ParameterRaw = share.console.ParameterRaw


class Console(share.console.ConsoleGen2):

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
