#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""SmartLink201 Test Programs."""

import re

import share


class Console(share.console.Base):

    """SmartLink201 console."""

    banner_lines = 12           # Startup banner lines
    # Console command prompt. Signals the end of response data.
    cmd_prompt = b'\r\x1b[1;32muart:~$ \x1b[m'
    # Console commands
    parameter = share.console.parameter
    cmd_data = {
        # Writable values
        'SERIAL': parameter.String(
            'smartlink serial', writeable=True, write_format='{1} {0}'),
        'PRODUCT-REV': parameter.String(
            'smartlink product-rev', writeable=True, write_format='{1} {0}'),
        'HARDWARE-REV': parameter.String(
            'smartlink hw-rev', writeable=True, write_format='{1} {0}'),
        'BATT_CAL': parameter.Float(
            'smartlink battery calibrate', scale=1000,
            writeable=True, write_format='{1} {0}'),
        # Action commands
        'REBOOT': parameter.String(
            'kernel reboot cold', writeable=True, write_format='{1}',
            write_expected=banner_lines),
        # Readable values
        'SW_VER': parameter.String(
            'smartlink sw-rev', read_format='{0}'),
        'MAC': parameter.String(
            'smartlink mac', read_format='{0}'),
        'BATT': parameter.String(
            'smartlink battery read', read_format='{0}'),
        }
    # Storage of response to analog query command
    analog_linecount = 18
    analog_regexp = re.compile('^([0-9]{1-2}):(0x0[0-9A-F]{3})$')
    analog_data = []        # Analog readings

    def __getitem__(self, key):
        """Read a value."""
        if key in self.analog_data:         # Try an analog value
            return self.analog_data[key]
        return super().__getitem__(key)     # Try the command table

    def brand(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '02A'
        @param hardware_rev Hardware revision from ECO eg: '02A'

        """
        self.action(None, expected=self.banner_lines)
        self['SERIAL'] = sernum
        self['PRODUCT-REV'] = product_rev
        self['HARDWARE-REV'] = hardware_rev

    def vbatt_cal(self, vbatt):
        """Calibrate Vbatt reading.

        @param vbatt Vbatt actual input value in mV

        """
        self['BATT_CAL'] = vbatt
        self['REBOOT'] = None

    def analog_read(self):
        """Read analog input raw values."""
        self.analog_data.clear()
        response = self.action(
            'smartlink analog', expected=self.analog_linecount)
        # Response lines are <DecimalIndex>:<HexValue> eg "9:0x0FFF"
        for line in response:
            match = self.analog_regexp.match(line)
            if match:
                index, hex = match.groups()
                index = int(index)
                name = self.tank_name(index)
                self.analog_data[name] = int(hex, 16)

    def tank_name(self, index):
        """Generate a Tank input name.

        @parm index Tank input index (0-15)
        @return Tank name string eg: "TANK1-1" to "TANK4-4"

        """
        return 'TANK{0}-{1}'.format((index // 4) + 1, (index % 4) + 1)
