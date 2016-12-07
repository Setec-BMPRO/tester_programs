#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 PIC processor console driver."""

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

    """Communications to IDS-500 console."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)
        self.cmd_data = {
            'PIC-SwRev': ParameterString(
                '?,I,1', read_format='{}'),
            'PIC-MicroTemp': ParameterString(
                '?,D,16', read_format='{}'),
            'PIC-Clear': ParameterString(
                '', read_format='{}'),
            'PIC-HwRev': ParameterString(
                '?,I,2', read_format='{}'),
            'PIC-SerNum': ParameterString(
                '?,I,3', read_format='{}'),
            'SwTstMode': ParameterString(
                '', writeable=True,
                write_format='S,:,{}'),
            'WriteHwRev': ParameterString(
                'S,@,', writeable=True,
                write_format='{1}{0}'),
            'WriteSerNum': ParameterString(
                'S,#,', writeable=True,
                write_format='{1}{0}'),
            }
        self.exp_cnt = 0

    def clear_port(self):
        """Discard unwanted strings when the port is opened"""
        self._logger.debug('Discard unwanted strings')
        self.exp_cnt = 1
        self['PIC-Clear']
        self['PIC-Clear']
        self['PIC-Clear']
        self.exp_cnt = 0

    def sw_test_mode(self):
        """Access Software Test Mode"""
        self.exp_cnt = 3
        self['SwTstMode'] = 0
        self['SwTstMode'] = 2230
        self.exp_cnt = 4
        self['SwTstMode'] = 42
        self.exp_cnt = 0

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response.

        Overrides BaseConsole().
        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param expected Expected number of responses.
        @return Response (None / String).

        """
        if command is not None:
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected=self.exp_cnt)

    def _write_command(self, command):
        """Write a command.

        Overrides BaseConsole().
        @param command Command string.

        """
        # Send the command with a '\r\n'
        cmd_data = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_data))
        self._port.write(cmd_data + b'\r\n')

    def _read_response(self, expected):
        """Read the response to a command.

        Overrides BaseConsole().
        @param expected Expected number of responses.
        @return Response (None / String).

        """
        all_response = []
        for _ in range(expected):
            data = self._port.readline()
            data = data.replace(b'\r', b'')   # Remove '\r'
            data = data.replace(b'\n', b'')   # Remove '\n'
            response = data.decode(errors='ignore')
            if len(response) == 0:
                response = None
            self._logger.debug('Response <-- %s', repr(response))
            all_response.append(response)
        return all_response
