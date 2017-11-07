#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck ARM processor console driver."""

import share


class Console(share.console.BadUart):

    """Communications to BatteryCheck console."""

    parameter = share.console.parameter
    cmd_data = {
        'UNLOCK': parameter.Boolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SW_VER': parameter.String(
            'SW-VERSION', read_format='{0}?'),
        'SER_ID': parameter.String(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='{1} {0}'),
        'VOLTAGE': parameter.Float(
            'X-BATTERY-VOLTS', scale=1000, read_format='{0} X?'),
        'CURRENT': parameter.Float(
            'X-BATTERY-CURRENT', scale=1000, read_format='{0} X?'),
        'SYS_EN': parameter.Float(
            'X-SYSTEM-ENABLE',
            writeable=True, readable=False, write_format='{0} {1} X!'),
        'ALARM-RELAY': parameter.Boolean(
            'ALARM-RELAY',
            writeable=True, readable=False, write_format='{0} {1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'mV', 'mA')
