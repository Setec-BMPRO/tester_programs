#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 ARM processor console driver."""

from share import console

Sensor = console.Sensor
# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Console(console.Base):

    """Communications to GEN8 console."""

    cmd_data = {
        'AcFreq': ParameterFloat(
            'X-AC-LINE-FREQUENCY', read_format='{0} X?'),
        'AcVolt': ParameterFloat(
            'X-AC-LINE-VOLTS', read_format='{0} X?'),
        '5V': ParameterFloat(
            'X-RAIL-VOLTAGE-5V', scale=1000, read_format='{0} X?'),
        '12V': ParameterFloat(
            'X-RAIL-VOLTAGE-12V', scale=1000, read_format='{0} X?'),
        '24V': ParameterFloat(
            'X-RAIL-VOLTAGE-24V', scale=1000, read_format='{0} X?'),
        'SwVer': ParameterString(
            'X-SOFTWARE-VERSION', read_format='{0} X?'),
        'SwBld': ParameterString(
            'X-BUILD-NUMBER', read_format='{0} X?'),
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
    ignore = (' ', 'Hz', 'Vrms', 'mV')

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
