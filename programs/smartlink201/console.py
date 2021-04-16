#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""SmartLink201 Test Programs."""

import re

import share


class Console(share.console.Base):

    """SmartLink201 console."""

    banner_lines = 5            # Startup banner lines
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
        # Calibration commands
        'BATT_CAL': parameter.Calibration(
            'smartlink battery calibrate', scale=1000),
        # Action commands
        'REBOOT': parameter.String(
            'kernel reboot cold', writeable=True, write_format='{1}'),
        # Readable values
        'SW-REV': parameter.String(
            'smartlink sw-rev', read_format='{0}'),
        'MAC': parameter.String(
            'smartlink mac', read_format='{0}'),
        'BATT': parameter.String(
            'smartlink battery read', read_format='{0}'),
        'TANK1-1': parameter.Float(
            'smartlink analog 1', read_format='{0}'),
        'TANK2-1': parameter.Float(
            'smartlink analog 5', read_format='{0}'),
        'TANK3-1': parameter.Float(
            'smartlink analog 9', read_format='{0}'),
        'TANK4-1': parameter.Float(
            'smartlink analog 13', read_format='{0}'),
        }
    re_blemac = re.compile('[0-9a-f]{12}')  # 'mac' response parser

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

    def get_mac(self):
        """Get the MAC address from the console

        @return 12 hex digit Bluetooth MAC address

        """
        result = ''
        try:
            mac = self['MAC']
            mac = mac.replace(':', '').lower()
            match = self.re_blemac.search(mac)
            if match:
                result = match.group(0)
        except share.console.Error:
            pass
        return result
