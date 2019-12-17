#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS-BTS Console driver."""

import re

import share


class Console(share.console.Base):

    """Communications to TRS-BTS console."""

    re_banner = re.compile('^ble addr ([0-9a-f]{12})$')
    # Number of lines in startup banner
    banner_lines = 3
    parameter = share.console.parameter
    cmd_data = {
        'UNLOCK': parameter.Boolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT', writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': parameter.String(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': parameter.String(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': parameter.String('SW-VERSION', read_format='{0}?'),
        # X-Register values
        'VBATT': parameter.Hex('TRS_BTS_AVG_BATT_MV', scale=1000),
        'VPIN': parameter.Hex('TRS_BTS_PIN_MV', scale=1000),
        # Calibration commands
        'VBATT_CAL': parameter.Calibration(
            'BATTV CAL', write_expected=2),
        # OverrideTo commands
        'MONITOR': parameter.Override('TRS2_MONITOR_EN_OVERRIDE'),
        'RED_LED': parameter.Override('TRS2_RED_LED_OVERRIDE'),
        'GREEN_LED': parameter.Override('TRS2_GREEN_LED_OVERRIDE'),
        'BLUE_LED': parameter.Override('TRS2_BLUE_LED_OVERRIDE'),
        'BLUETOOTH': parameter.Override('TRS2_BLUETOOTH_EN_OVERRIDE'),
        }
    override_commands = (
        'MONITOR', 'RED_LED', 'GREEN_LED', 'BLUE_LED')

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self.banner()
        self['UNLOCK'] = True
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True

    def banner(self):
        """Flush the startup banner lines."""
        self.action(None, expected=self.banner_lines)

    def override(self, state=parameter.OverrideTo.normal):
        """Manually override functions of the unit.

        @param state OverrideTo enumeration

        """
        for func in self.override_commands:
            self[func] = state

    def get_mac(self):
        """Get the MAC address from the console

        @return 12 hex digit Bluetooth MAC address

        """
        result = ''
        try:
            mac = self.action(None, delay=1.5, expected=self.banner_lines)
            if self.banner_lines > 1:
                mac = mac[0]
            mac = mac.replace(':', '')
            match = self.re_banner.match(mac)
            if match:
                result = match.group(1)
        except share.console.Error:
            pass
        return result
