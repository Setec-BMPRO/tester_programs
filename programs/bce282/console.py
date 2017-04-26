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


class Console(console.Variable, console.BaseConsole):

    """Communications to BCE282 console."""

    # Console command prompt. Signals the end of output data.
    cmd_prompt = b'\r>'
    # Command suffix between echo of a command and the response.
    res_suffix = b'->'
    # Auto add prompt to puts strings
    puts_prompt = '\r\n>'
    expected = 0
    cmd_data = {
        '0 ECHO': ParameterString(
            '0 echo', read_format='{0}'),
        'UNLOCK': ParameterString(
            '$deadbea7 unlock', read_format='{0}'),
        'NV-WRITE-RES': ParameterString(
            'nv-factory-write restart', read_format='{0}'),
        'NV-WRITE': ParameterString(
            'nv-factory-write', read_format='{0}'),
        'TEST-MODE': ParameterString(
            'test-mode-enable', read_format='{0}'),
        'FL-RELOAD': ParameterString(
            'adc-filter-reload', read_format='{0}'),
#        'MSP-STATUS': ParameterFloat(
#            'nv-status PRINT', read_format='{0}'),
        'MSP-STATUS': ParameterString(
            'nv-status PRINT', read_format='{0}'),
        'MSP-VOUT': ParameterFloat(
            'x-supply-voltage x@ print', read_format='{0}', scale=1000),
        'CAL-V': ParameterFloat(
            ' cal-vset PRINT', writeable=True, write_format='{0}{1}',
            read_format='{0}', minimum=0, maximum=15000, scale=1000),
        'VER': ParameterString(
            'x-software-version x@ PRINT', read_format='{0}'),
        }

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)

    def setup(self):
        """Setup console for calibration."""
#        self['0 ECHO']
        self['UNLOCK']
#        self['NV-WRITE-RES']
#        self['0 ECHO']
#        self['UNLOCK']

    def test_mode(self):
        """Enable Manual Mode"""
        self['TEST-MODE']

    def filter_reload(self):
        """Reset internal filters."""
        self['FL-RELOAD']

    def action(self, command=None, delay=0, expected=0):
        """Overrides action() in BaseConsole class."""
        if command is not None:
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected=self.expected)

    def _write_command(self, command):
        """Overrides _write_command() in BaseConsole class."""
        # Send the command with a '\r'
        cmd_bytes = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_bytes))
        self.port.write(cmd_bytes + b'\r')

#    def _read_response(self, expected):
#        """Read the response to a command.
#
#        Overrides BaseConsole().
#        @param expected Expected number of responses.
#        @return Response (None / List of String).
#
#        """
#        all_response = []
#        for _ in range(expected):
#            data = self.port.readline()
#            data = data.replace(b'\r', b'')   # Remove '\r'
#            data = data.replace(b'\n', b'')   # Remove '\n'
#            response = data.decode(errors='ignore')
#            if len(response) == 0:
#                response = None
#            self._logger.debug('Response <-- %s', repr(response))
#            all_response.append(response)
#        return all_response
