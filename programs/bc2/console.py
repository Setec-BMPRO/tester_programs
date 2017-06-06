#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Console driver."""

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


class Console(console.Variable, console.BadUartConsole):

    """Communications to BC2 console."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BadUartConsole.__init__(self, port, verbose)
        # Auto add prompt to puts strings
        self.puts_prompt = '\r\n> '
        self.cmd_data = {
            'UNLOCK': ParameterBoolean('$DEADBEA7 UNLOCK',
                writeable=True, readable=False, write_format='{1}'),
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
