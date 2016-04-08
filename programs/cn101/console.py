#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Console driver."""

from ..share import console

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
# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF
# Bluetooth ready controlled by STATUS bit 27
_BLE_ON = (1 << 27)
_BLE_OFF = ~_BLE_ON & 0xFFFFFFFF


class Console(console.Variable, console.BadUartConsole):

    """Communications to CN101 console."""

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        self.cmd_data = {
            'UNLOCK': ParameterString('UNLOCK',
                writeable=True, readable=False, write_format='{} {}'),
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
            'CAN_BIND': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=(1 << 28)),
            'CAN': ParameterString('CAN',
                writeable=True, write_format='"{} {}'),
            'TANK1': ParameterFloat('TANK_1_LEVEL'),
            'TANK2': ParameterFloat('TANK_2_LEVEL'),
            'TANK3': ParameterFloat('TANK_3_LEVEL'),
            'TANK4': ParameterFloat('TANK_4_LEVEL'),
            'ADC_SCAN': ParameterFloat(
                'ADC_SCAN_INTERVAL_MSEC', writeable=True),
            }

    def testmode(self, state):
        """Enable or disable Test Mode."""
        self._logger.debug('Test Mode = %s', state)
        reply = self['STATUS']
        if state:
            value = _TEST_ON | reply
        else:
            value = _TEST_OFF & reply
        self['STATUS'] = value

    def can_testmode(self, state):
        """Enable or disable CAN Test Mode.

        Once test mode is active, all CAN packets received will display onto
        the console. This means that the Command-Response protocol cannot
        be used any more as it breaks with the extra asynchronous messages.

        """
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = _CAN_ON | reply
        else:
            value = _CAN_OFF & reply
        self['STATUS'] = value
