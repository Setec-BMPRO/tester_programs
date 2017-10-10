#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLE2CAN Console driver."""

from share import console

Sensor = console.Sensor
# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean


class Console(console.BaseConsole):

    """Communications to BLE2CAN console."""

    cmd_data = {
        'NVDEFAULT': ParameterBoolean(
            'NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SER_ID': ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': ParameterString(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': ParameterString('SW-VERSION', read_format='{0}?'),
        'BT_MAC': ParameterString('BLE-MAC', read_format='{0}?'),
        }
