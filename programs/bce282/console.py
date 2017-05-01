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


class Console(console.Variable, console.BadUartConsole):

    """Communications to BCE282 console."""

    # Console command prompt. Signals the end of output data.
    cmd_prompt = b'\r> '
    # Command suffix between echo of a command and the response.
    res_suffix = b' -> '
    # Auto add prompt to puts strings
    puts_prompt = '\r> '
    expected = 0
    cmd_data = {
        'ECHO': ParameterBoolean(
            'echo', writeable=True, write_format='{0} {1}', read_format='{0}'),
        'UNLOCK': ParameterBoolean(
            '$deadbea7 unlock', writeable=True, write_format='{1}'),
        'NV-WRITE': ParameterString(
            'nv-factory-write', read_format='{0}'),
        'TEST-MODE': ParameterBoolean(
            'test-mode-enable', writeable=True, write_format='{1}'),
        'FL-RELOAD': ParameterBoolean(
            'adc-filter-reload', writeable=True, write_format='{1}'),
        'MSP-STATUS': ParameterFloat(
            'nv-status PRINT', read_format='{0}'),
        # 24V model needs scaling down as both models respond with 12V output.
        'MSP-VOUT': ParameterFloat(
            'x-supply-voltage x@ print', read_format='{0}', scale=500),
        # 24V model needs scaling down as it needs to be calibrated with 12V output.
        'CAL-V': ParameterFloat(
            'cal-vset PRINT', writeable=True, write_format='{0} {1}',
            read_format='{0}', minimum=0, maximum=15000, scale=500),
        'BATT': ParameterBoolean(
            'battery-switch', writeable=True, write_format='{0} {1}', read_format='{0}'),
        }

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BadUartConsole.__init__(self, port, verbose)

    def setup(self):
        """Setup console for calibration."""
        self['ECHO'] = True
        self['UNLOCK'] = True
        self['NV-WRITE']
        self['ECHO'] = True
        self['UNLOCK'] = True

    def test_mode(self):
        """Enable Manual Mode"""
        self['TEST-MODE'] = True

    def filter_reload(self):
        """Reset internal filters."""
        self['FL-RELOAD'] = True

#    def action(self, command=None, delay=0, expected=0):
#        """Overrides action() in BaseConsole class."""
#        if command is not None:
#            self._write_command(command)
#        if delay:
#            time.sleep(delay)
#        return self._read_response(expected=self.expected)
#
#    def _write_command(self, command):
#        """Overrides _write_command() in BaseConsole class."""
#        # Send the command with a '\r'
#        cmd_bytes = command.encode()
#        self._logger.debug('Cmd --> %s', repr(cmd_bytes))
#        self.port.write(cmd_bytes + b'\r')

