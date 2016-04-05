#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 ARM processor console driver."""

from ..share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat


class Console(console.ConsoleGen1):

    """Communications to GEN8 console."""

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        rfmt = '{} X?'      # 1st generation console read format string
        self.cmd_data = {
            'ARM-AcDuty': ParameterFloat(
                'X-AC-DETECTOR-DUTY', read_format=rfmt),
            'ARM-AcPer': ParameterFloat(
                'X-AC-DETECTOR-PERIOD', scale=1000, read_format=rfmt),
            'ARM-AcFreq': ParameterFloat(
                'X-AC-LINE-FREQUENCY', read_format=rfmt),
            'ARM-AcVolt': ParameterFloat('X-AC-LINE-VOLTS', read_format=rfmt),
            'ARM-PfcTrim': ParameterFloat('X-PFC-TRIM', read_format=rfmt),
            'ARM-12VTrim': ParameterFloat(
                'X-CONVERTER-VOLTS-TRIM', read_format=rfmt),
            'ARM-5V': ParameterFloat(
                'X-RAIL-VOLTAGE-5V', scale=1000, read_format=rfmt),
            'ARM-12V': ParameterFloat(
                'X-RAIL-VOLTAGE-12V', scale=1000, read_format=rfmt),
            'ARM-24V': ParameterFloat(
                'X-RAIL-VOLTAGE-24V', scale=1000, read_format=rfmt),
            'ARM-5Vadc': ParameterFloat('X-ADC-5V-RAIL', read_format=rfmt),
            'ARM-12Vadc': ParameterFloat('X-ADC-12V-RAIL', read_format=rfmt),
            'ARM-24Vadc': ParameterFloat('X-ADC-24V-RAIL', read_format=rfmt),
            'ARM_SwVer': ParameterString(
                'X-SOFTWARE-VERSION', read_format=rfmt),
            'ARM_SwBld': ParameterString('X-BUILD-NUMBER', read_format=rfmt),
            'CAL_PFC': ParameterFloat(
                'CAL-PFC-BUS-VOLTS', writeable=True, readable=False,
                scale=1000, write_format='{0} {1}'),
            'CAL_12V': ParameterFloat(
                'CAL-CONVERTER-VOLTS', writeable=True, readable=False,
                scale=1000, write_format='{0} {1}'),
            }
        # Strings to ignore in responses
        self.ignore = (' %', ' ms', ' Hz', ' Vrms', ' mV', ' Counts')
