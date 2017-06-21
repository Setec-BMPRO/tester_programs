#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck ARM processor console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat


class Console(console.BadUartConsole):

    """Communications to BatteryCheck console."""

    # Auto add prompt to puts strings
    puts_prompt = '\r\n> '
    cmd_data = {
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
    ignore = (' ', 'mV', 'mA')
