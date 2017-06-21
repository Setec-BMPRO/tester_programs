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


class ConsoleResponseError():

    """Console Response Error."""


class Console(console.BadUartConsole):

    """Communications to BCE282 console."""

    # Console command prompt. Signals the end of output data.
    cmd_prompt = b'\r> '
    # Command suffix between echo of a command and the response.
    res_suffix = b' -> '
    # Auto add prompt to puts strings
    puts_prompt = '\r> '
    cmd_data = {
        'ECHO': ParameterBoolean(
            'echo', writeable=True, write_format='{0} {1}', read_format='{0}'),
        'UNLOCK': ParameterBoolean(
            '$deadbea7 unlock', writeable=True, write_format='{1}'),
        'NV-WRITE': ParameterBoolean(
            'nv-factory-write', writeable=True, write_format='{1}'),
        'RESTART': ParameterBoolean(
            'restart', writeable=True, write_format='{1}'),
        'TEST-MODE': ParameterBoolean(
            'test-mode-enable', writeable=True, write_format='{1}'),
        'FL-RELOAD': ParameterBoolean(
            'adc-filter-reload', writeable=True, write_format='{1}'),
        'MSP-STATUS': ParameterFloat(
            'nv-status PRINT', read_format='{0}'),
        'MSP-VOUT': ParameterFloat(
            'x-supply-voltage x@ print', read_format='{0}'),
        'CAL-V': ParameterFloat(
            'cal-vset', writeable=True, write_format='{0} {1}',
            read_format='{0}', minimum=0, maximum=15000),
        'PASSWD': ParameterString(
            'bsl-password', read_format='{0}'),
        }

    def config(self, value):
        """Configure scale values for each model."""
        self.cmd_data['MSP-VOUT'].scale = value
        self.cmd_data['CAL-V'].scale = value

    def setup(self):
        """Setup console for calibration."""
        self['ECHO'] = True
        self['UNLOCK'] = True
        self['NV-WRITE'] = True
        # RESTART acts without sending a prompt, so we add one
        self.port.puts(self.puts_prompt, priority=True)
        self['RESTART'] = True
        self.action('', expected=4)     # Consume the startup banner lines
        self['ECHO'] = True
        self['UNLOCK'] = True

    def test_mode(self):
        """Enable Manual Mode"""
        self['TEST-MODE'] = True
        time.sleep(0.1)

    def filter_reload(self):
        """Reset internal filters."""
        self['FL-RELOAD'] = True
        time.sleep(1)
