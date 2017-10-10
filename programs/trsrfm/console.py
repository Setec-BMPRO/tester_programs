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


class Console(console.BaseConsole):

    """Communications to TRSRFM console."""

    cmd_data = {
        'NVDEFAULT': ParameterBoolean(
            'NV-DEFAULT', writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': ParameterString(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': ParameterString(
            'SW-VERSION', read_format='{0}?'),
        'BT_MAC': ParameterString(
            'BLE-MAC', read_format='{0}?'),
        'RED_LED': ParameterFloat(
            'TRSRFM_RED_LED_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'GREEN_LED': ParameterFloat(
            'TRSRFM_GREEN_LED_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'BLUE_LED': ParameterFloat(
            'TRSRFM_BLUE_LED_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'BLUETOOTH': ParameterFloat(
            'TRSRFM_BLUETOOTH_EN_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'FAULT_CODE': ParameterHex('TRSRFM_FAULT_CODE_BITS',
            minimum=0, maximum=0x00000003),
        }

    def override(self, state=0):
        """Manually override functions of the unit.

        ON: state = 2
        OFF: state = 1
        NORMAL OPERATION: state = 0
        """
        self._logger.debug('Override state = %s', state)
        for func in ('RED_LED', 'GREEN_LED', 'BLUE_LED'):
            self[func] = state
