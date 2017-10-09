#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 ARM processor console driver."""

from share import console

Sensor = console.Sensor
# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Console(console.BaseConsole):

    """Communications to SX-750 console."""

    cmd_data = {
        'ARM-AcFreq': ParameterFloat(
            'X-AC-LINE-FREQUENCY', read_format='{0} X?'),
        'ARM-AcVolt': ParameterFloat(
            'X-AC-LINE-VOLTS', read_format='{0} X?'),
        'ARM-12V': ParameterFloat(
            'X-RAIL-VOLTAGE-12V', scale=1000, read_format='{0} X?'),
        'ARM-24V': ParameterFloat(
            'X-RAIL-VOLTAGE-24V', scale=1000, read_format='{0} X?'),
        'ARM_SwVer': ParameterString(
            'X-SOFTWARE-VERSION', read_format='{0} X?'),
        'ARM_SwBld': ParameterString(
            'X-BUILD-NUMBER', read_format='{0} X?'),
        'FAN_SET': ParameterFloat(
            'X-TEMPERATURE-CONTROLLER-SETPOINT',
            writeable=True,
            write_format='{0} {1} X!'),
        'CAL_PFC': ParameterFloat(
            'CAL-PFC-BUS-VOLTS',
            writeable=True, readable=False, scale=1000,
            write_format='{0} {1}'),
        'UNLOCK': ParameterBoolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'Hz', 'Vrms', 'mV')

    def calpfc(self, voltage):
        """Issue PFC calibration commands."""
        self['CAL_PFC'] = voltage
        self['NVWRITE'] = True
