#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRSRFM Console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex
ParameterCAN = console.ParameterCAN
ParameterRaw = console.ParameterRaw

# Test mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF
# Bluetooth ready controlled by STATUS bit 27
_BLE_ON = (1 << 27)
_BLE_OFF = ~_BLE_ON & 0xFFFFFFFF


class Console(console.BaseConsole):

    """Communications to TRSRFM console."""

    # Auto add prompt to puts strings
    puts_prompt = '\r\n> '
    cmd_data = {
        'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean('NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SER_ID': ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{} {}'),
        'HW_VER': ParameterString(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': ParameterString('SW-VERSION', read_format='{}?'),
        'BT_MAC': ParameterString('BLE-MAC', read_format='{}?'),
        }
