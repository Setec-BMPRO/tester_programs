#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck ARM processor console driver."""

import share

# Some easier to use short names
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat


class Console(share.console.BadUart):

    """Communications to BatteryCheck console."""

    cmd_data = {
        'UNLOCK': ParameterBoolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SW_VER': ParameterString(
            'SW-VERSION', read_format='{0}?'),
        'SER_ID': ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='{1} {0}'),
        'VOLTAGE': ParameterFloat(
            'X-BATTERY-VOLTS', scale=1000, read_format='{0} X?'),
        'CURRENT': ParameterFloat(
            'X-BATTERY-CURRENT', scale=1000, read_format='{0} X?'),
        'SYS_EN': ParameterFloat(
            'X-SYSTEM-ENABLE',
            writeable=True, readable=False, write_format='{0} {1} X!'),
        'ALARM-RELAY': ParameterBoolean(
            'ALARM-RELAY',
            writeable=True, readable=False, write_format='{0} {1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'mV', 'mA')
