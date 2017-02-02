#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck ARM processor console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat


class Console(console.Variable, console.BadUartConsole):

    """Communications to BatteryCheck console."""

    def __init__(self, port):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BadUartConsole.__init__(self, port)
        # Auto add prompt to puts strings
        self.puts_prompt = '\r\n> '
        self.cmd_data = {
            'UNLOCK': ParameterBoolean('$DEADBEA7 UNLOCK',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            'SW_VER': ParameterString('SW-VERSION', read_format='{}?'),
            'SER_ID': ParameterString(
                'SET-SERIAL-ID', writeable=True, readable=False,
                write_format='{1} {0}'),
            'VOLTAGE': ParameterFloat(
                'X-BATTERY-VOLTS', scale=1000, read_format='{} X?'),
            'CURRENT': ParameterFloat(
                'X-BATTERY-CURRENT', scale=1000, read_format='{} X?'),
            'SYS_EN': ParameterFloat('X-SYSTEM-ENABLE',
                writeable=True, readable=False, write_format='{} {} X!'),
            'ALARM-RELAY': ParameterBoolean('ALARM-RELAY',
                writeable=True, readable=False, write_format='{} {}'),
            }
        # Strings to ignore in responses
        self.ignore = (' ', 'mV', 'mA')
