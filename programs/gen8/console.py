#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 ARM processor console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Console(console.Variable, console.BaseConsole):

    """Communications to GEN8 console."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)
        # Auto add prompt to puts strings
        self.puts_prompt = '\r> '
        rfmt = '{} X?'      # 1st generation console read format string
        self.cmd_data = {
            'AcFreq': ParameterFloat(
                'X-AC-LINE-FREQUENCY', read_format=rfmt),
            'AcVolt': ParameterFloat('X-AC-LINE-VOLTS', read_format=rfmt),
            '5V': ParameterFloat(
                'X-RAIL-VOLTAGE-5V', scale=1000, read_format=rfmt),
            '12V': ParameterFloat(
                'X-RAIL-VOLTAGE-12V', scale=1000, read_format=rfmt),
            '24V': ParameterFloat(
                'X-RAIL-VOLTAGE-24V', scale=1000, read_format=rfmt),
            'SwVer': ParameterString(
                'X-SOFTWARE-VERSION', read_format=rfmt),
            'SwBld': ParameterString('X-BUILD-NUMBER', read_format=rfmt),
            'CAL_PFC': ParameterFloat(
                'CAL-PFC-BUS-VOLTS', writeable=True, readable=False,
                scale=1000, write_format='{0} {1}'),
            'CAL_12V': ParameterFloat(
                'CAL-CONVERTER-VOLTS', writeable=True, readable=False,
                scale=1000, write_format='{0} {1}'),
            'UNLOCK': ParameterBoolean('$DEADBEA7 UNLOCK',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            }
        # Strings to ignore in responses
        self.ignore = (' ', 'Hz', 'Vrms', 'mV')

    def calpfc(self, voltage):
        """Issue PFC calibration commands.

        @param voltage Measured PFC bus voltage

        """
        self['CAL_PFC'] = voltage
        self['NVWRITE'] = True

    def cal12v(self, voltage):
        """Issue 12V calibration commands.

        @param voltage Measured 12V rail voltage

        """
        self['CAL_12V'] = voltage
        self['NVWRITE'] = True
