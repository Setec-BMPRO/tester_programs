#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""IDS-500 PIC processor console driver."""

import time
import share


class Console(share.console.Base):

    """Communications to IDS-500 console."""

    # Magic numbers to unlock test mode
    _testmode_magic_1 = 0
    _testmode_magic_2 = 2230
    _testmode_magic_3 = 42
    parameter = share.console.parameter
    cmd_data = {
        'PIC-SwRev': parameter.String('?,I,1', read_format='{0}'),
        'PIC-MicroTemp': parameter.String('?,D,16', read_format='{0}'),
        'PIC-Clear': parameter.String('', read_format='{0}'),
        'PIC-HwRev': parameter.String('?,I,2', read_format='{0}'),
        'PIC-SerNum': parameter.String('?,I,3', read_format='{0}'),
        'SwTstMode': parameter.String(
            'S,:,', writeable=True, write_format='{1}{0}'),
        'WriteHwRev': parameter.String(
            'S,@,', writeable=True, write_format='{1}{0}'),
        'WriteSerNum': parameter.String(
            'S,#,', writeable=True, write_format='{1}{0}'),
        }
    expected = 0

    def clear_port(self):
        """Discard unwanted strings when the port is opened"""
        self._logger.debug('Discard unwanted strings')
        self.expected = 1
        self['PIC-Clear']
        self['PIC-Clear']
        self['PIC-Clear']
        self.expected = 0

    def sw_test_mode(self):
        """Access Software Test Mode"""
        self.expected = 3
        self['SwTstMode'] = self._testmode_magic_1
        self['SwTstMode'] = self._testmode_magic_2
        self.expected = 4
        self['SwTstMode'] = self._testmode_magic_3
        self.expected = 0

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response.

        Overrides BaseConsole().
        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param expected Expected number of responses.
        @return Response (None / List of String).

        """
        if command is not None:
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected=self.expected)

    def _write_command(self, command):
        """Write a command.

        Overrides BaseConsole().
        @param command Command string.

        """
        cmd_data = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_data))
        self.port.write(cmd_data + b'\r\n')

    def _read_response(self, expected):
        """Read the response to a command.

        Overrides BaseConsole().
        @param expected Expected number of responses.
        @return Response (None / List of String).

        """
        all_response = []
        for _ in range(expected):
            data = self.port.readline()
            data = data.replace(b'\r', b'')
            data = data.replace(b'\n', b'')
            response = data.decode(errors='ignore')
            if len(response) == 0:
                response = None
            self._logger.debug('Response <-- %s', repr(response))
            all_response.append(response)
        response = all_response
        response_count = len(response)
        if response_count == 1:     # Reduce list of 1 string to a string
            response = response[0]
        if response_count == 0:     # Reduce empty list to None
            response = None
        return response
