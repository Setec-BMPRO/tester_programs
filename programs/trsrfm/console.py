#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""TRS-RFM Console driver."""

import re

import share


class Console(share.console.Base):

    """Communications to TRS-RFM console."""

    re_blemac = re.compile(r"[0-9a-f]{12}")
    # Number of lines in startup banner
    banner_lines = 3
    parameter = share.console.parameter
    cmd_data = {
        "NVDEFAULT": parameter.Boolean(
            "NV-DEFAULT", writeable=True, readable=False, write_format="{1}"
        ),
        "NVWRITE": parameter.Boolean(
            "NV-WRITE", writeable=True, readable=False, write_format="{1}"
        ),
        "SER_ID": parameter.String(
            "SET-SERIAL-ID", writeable=True, readable=False, write_format='"{0} {1}'
        ),
        "HW_VER": parameter.String(
            "SET-HW-VER",
            writeable=True,
            readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}',
        ),
        "SW_VER": parameter.String("SW-VERSION", read_format="{0}?"),
        "BT_MAC": parameter.String("BLE-MAC", read_format="{0}?"),
        # OverrideTo commands
        "RED_LED": parameter.Override("TRS_RFM_RED_LED_OVERRIDE"),
        "GREEN_LED": parameter.Override("TRS_RFM_GREEN_LED_OVERRIDE"),
        "BLUE_LED": parameter.Override("TRS_RFM_BLUE_LED_OVERRIDE"),
    }
    override_commands = (
        "RED_LED",
        "GREEN_LED",
        "BLUE_LED",
    )

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self.banner()
        self["HW_VER"] = hw_ver
        self["SER_ID"] = sernum
        self["NVDEFAULT"] = True
        self["NVWRITE"] = True

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
        result = ""
        try:
            mac = self["BT_MAC"]
            mac = mac.replace(":", "").lower()
            match = self.re_blemac.search(mac)
            if match:
                result = match.group(0)
        except share.console.Error:
            pass
        return result
