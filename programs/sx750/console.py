#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 ARM processor console driver."""

from ..share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Console(console.Variable, console.BaseConsole):

    """Communications to SX-750 console."""

    def __init__(self, port, timeout=2.0, verbose=False):
        """Create console instance."""
        super().__init__(port, timeout, verbose)
        rfmt = '{} X?'      # 1st generation console read format string
        self.cmd_data = {
            'ARM-AcFreq': ParameterFloat(
                'X-AC-LINE-FREQUENCY', read_format=rfmt),
            'ARM-AcVolt': ParameterFloat('X-AC-LINE-VOLTS', read_format=rfmt),
            'ARM-12V': ParameterFloat(
                'X-RAIL-VOLTAGE-12V', scale=1000, read_format=rfmt),
            'ARM-24V': ParameterFloat(
                'X-RAIL-VOLTAGE-24V', scale=1000, read_format=rfmt),
            'ARM_SwVer': ParameterString(
                'X-SOFTWARE-VERSION', read_format=rfmt),
            'ARM_SwBld': ParameterString('X-BUILD-NUMBER', read_format=rfmt),
            'CAL_PFC': ParameterFloat(
                'CAL-PFC-BUS-VOLTS', writeable=True, readable=False,
                scale=1000, write_format='{0} {1}'),
            'UNLOCK': ParameterString('UNLOCK',
                writeable=True, readable=False, write_format='{} {}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            }
        # Strings to ignore in responses
        self.ignore = (' ', 'Hz', 'Vrms', 'mV')
