#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""IDS-500 PIC processor console driver."""

import time

import share
import tester


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

    def sw_test_mode(self):
        """Access Software Test Mode."""
        self.port.write(b'\r\n' * 3)    # 'wake up' the serial interface
        time.sleep(1)
        self.port.reset_input_buffer()
        self.expected = 3
        self['SwTstMode'] = self._testmode_magic_1
        self['SwTstMode'] = self._testmode_magic_2
        self.expected = 4
        self['SwTstMode'] = self._testmode_magic_3
        self.expected = 0

    def action(self, command=None, delay=0, expected=0):
        """Send a command, and read the response.

        @param command Command string
        @param delay Delay between sending command and reading response
        @param expected Expected number of responses
        @return Response (None / List of String)

        """
        self.port.reset_input_buffer()
        if command:
            self._write_command(command)
        if delay:
            time.sleep(delay)
        return self._read_response(expected=self.expected)

    def _write_command(self, command):
        """Write a command.

        @param command Command string

        """
        cmd_data = command.encode()
        self._logger.debug('Cmd --> %s', repr(cmd_data))
        self.port.write(cmd_data + b'\r\n')

    def _read_response(self, expected):
        """Read the response to a command, ignoring empty lines.

        @param expected Expected number of response lines
        @return Response (None / String / List of Strings)

        """
        all_response = []           # Buffer for response lines
        buf = bytearray()           # Buffer for the response bytes
        for _ in range(expected):
            buf.clear()
            while b'\n' not in buf:
                data = self.port.read(1)
                if self.verbose:
                    self._logger.debug('Read <-- %s', repr(data))
                if not data:        # No data means a timeout
                    comms = tester.Measurement(
                        tester.LimitRegExp(
                            'Action', 'ok', doc='Command succeeded'),
                        tester.sensor.MirrorReadingString())
                    comms.sensor.store('No response')
                    comms.measure() # Generates a test FAIL result
                buf += data
            self._logger.debug('Response <-- %s', repr(buf))
            buf = buf.replace(b'\r', b'')
            buf = buf.replace(b'\n', b'')
            response = buf.decode(errors='ignore')
            if response:
                all_response.append(response)
        response = all_response
        response_count = len(response)
        if response_count == 1:     # Reduce list of 1 string to a string
            response = response[0]
        elif not response_count:    # Reduce empty list to None
            response = None
        return response
