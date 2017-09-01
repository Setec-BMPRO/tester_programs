#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Console driver."""

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


#class Console(console.BadUartConsole):
class Console(console.BaseConsole):

    """Communications to TRS2 console."""

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
        'STATUS': ParameterHex('STATUS', writeable=True,
            minimum=0, maximum=0xF0000000),
        'BR_LIGHT': ParameterFloat(
            'TRS2_BRAKE_LIGHT_EN_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'MONITOR': ParameterFloat(
            'TRS2_MONITOR_EN_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'RED': ParameterFloat(
            'TRS2_RED_LED_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'GREEN': ParameterFloat(
            'TRS2_GREEN_LED_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'BLUE': ParameterFloat(
            'TRS2_BLUE_LED_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'BLUETOOTH': ParameterFloat(
            'TRS2_BLUETOOTH_EN_OVERRIDE', writeable=True,
            minimum=0, maximum=2),
        'VBATT': ParameterFloat(
            'TRS2_BATT_MV', scale=1000),
        'FAULT_CODE': ParameterString(
            'TRS2_FAULT_CODE_BITS', ),
        'BATT_CHANGE': ParameterString(
            'TRS2_BATT_CHANGE', ),
        'STATE': ParameterString(
            'TRS2_STATE', ),
        }

    def override(self, state=0):
        """Manually override functions of the unit.

        ON: state = 2
        OFF: state = 1
        NORMAL OPERATION: state = 0
        """
        self._logger.debug('Override state = %s', state)
        for func in ('BR_LIGHT', 'MONITOR', 'RED', 'GREEN', 'BLUE'):
            self[func] = state
