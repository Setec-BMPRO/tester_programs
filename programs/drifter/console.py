#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat


class Console(console.Variable, console.BadUartConsole):

    """Communications to Drifter console."""

    def __init__(self, port):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BadUartConsole.__init__(self, port, verbose=False)
        self.cmd_data = {
            'UNLOCK': ParameterString('UNLOCK',
                writeable=True, readable=False, write_format='{} {}'),
            'NVDEFAULT': ParameterBoolean('NV-WRITE-DEFAULT',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            'NVSTATUS': ParameterFloat('NV-STATUS PRINT', read_format='{}'),
            'RESTART': ParameterBoolean('RESTART',
                writeable=True, readable=False, write_format='{1}'),
            'APS_DISABLE': ParameterFloat('APS-DISABLE',
                writeable=True, readable=False, write_format='{} {}'),
            'CAL_RELOAD': ParameterBoolean('CAL-RELOAD',
                writeable=True, readable=False, write_format='{1}'),
            'CAL_I_ZERO': ParameterBoolean('CAL-I-ZERO',
                writeable=True, readable=False, write_format='{1}'),
            'CAL_I_SLOPE': ParameterFloat('CAL-I-SLOPE',
                writeable=True, readable=False, scale=1000,
                minimum=-200000, maximum=200000,
                write_format='{} {}'),
            'CAL_V_SLOPE': ParameterFloat('CAL-V-SLOPE',
                writeable=True, readable=False, scale=1000,
                write_format='{} {}'),
            'CAL_OFFSET_CURRENT': ParameterFloat('X-CAL-OFFSET-CURRENT',
                writeable=True, scale=1, minimum=-1000,
                write_format='{} {} X!', read_format='{} X?'),
            'VOLTAGE': ParameterFloat('X-VOLTS-FILTERED',
                scale=1000, read_format='{} X?'),
            'CURRENT': ParameterFloat('X-CURRENT-FILTERED',
                scale=1000, read_format='{} X?'),
            'ZERO_CURRENT': ParameterFloat('X-CURRENT-FILTERED',
                scale=1, read_format='{} X?'),
            'ZERO-CURRENT-DISPLAY-THRESHOLD': ParameterFloat(
                'X-ZERO-CURRENT-DISPLAY-THRESHOLD',
                writeable=True, scale=1, minimum=-1000,
                write_format='{} {} X!', read_format='{} X?'),
            'V_FACTOR': ParameterFloat('X-CAL-FACTOR-VOLTS',
                read_format='{} X?'),
            'I_FACTOR': ParameterFloat('X-CAL-FACTOR-CURRENT',
                read_format='{} X?'),
            }
        # Strings to ignore in responses
        self.ignore = (' ', )
