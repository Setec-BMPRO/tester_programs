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
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'SwVer': ParameterRaw('', func=self.version),
            }
