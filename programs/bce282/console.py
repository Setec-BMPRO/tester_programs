#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282 MSP430 processor console driver."""

import time
from share import console

Sensor = console.Sensor
# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Console(console.BaseConsole):

    """Communications to BCE282 console."""

    # Console command prompt. Signals the end of output data.
    cmd_prompt = b'\r> '
    # Command suffix between echo of a command and the response.
    res_suffix = b' -> '
    # Auto add prompt to puts strings
    puts_prompt = '\r> '
    cmd_data = {
        'ECHO': ParameterBoolean(
            'ECHO', writeable=True, write_format='{0} {1}', read_format='{0}'),
        'UNLOCK': ParameterBoolean(
            '$DEADBEA7 UNLOCK', writeable=True, write_format='{1}'),
        'NV-WRITE': ParameterBoolean(
            'NV-FACTORY-WRITE', writeable=True, write_format='{1}'),
        'RESTART': ParameterBoolean(
            'RESTART', writeable=True, write_format='{1}',
            write_expected=5),  # 5 lines of startup banner
        'TEST-MODE': ParameterBoolean(
            'TEST-MODE-ENABLE', writeable=True, write_format='{1}'),
        'FL-RELOAD': ParameterBoolean(
            'ADC-FILTER-RELOAD', writeable=True, write_format='{1}'),
        'MSP-STATUS': ParameterFloat(
            'NV-STATUS PRINT', read_format='{0}'),
        'MSP-VOUT': ParameterFloat(
            'X-SUPPLY-VOLTAGE X@ PRINT', read_format='{0}'),
        'CAL-V': ParameterFloat(
            'CAL-VSET', writeable=True, write_format='{0} {1}',
            read_format='{0}', minimum=12000, maximum=15000),
        'PASSWD': ParameterString(
            'BSL-PASSWORD', read_format='{0}'),
        }

    def config(self, value):
        """Configure scale values for each model."""
        self.cmd_data['MSP-VOUT'].scale = value
        self.cmd_data['CAL-V'].scale = value

    def open(self):
        """Open & setup console for calibration."""
        super().open()
        self['ECHO'] = True
        self['UNLOCK'] = True
        self['NV-WRITE'] = True
        self['RESTART'] = True
        self['ECHO'] = True
        self['UNLOCK'] = True
        self['TEST-MODE'] = True

    def filter_reload(self):
        """Reset internal filters."""
        self['FL-RELOAD'] = True
        time.sleep(1)

    def action(self, command=None, delay=0.0, expected=0):
        """Send a command, and read the response (force a 0.1s delay).

        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises ConsoleError.

        """
        return super().action(command, 0.1, expected)
