#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""TRS-BTx Console driver."""

import re
import time

import share


class Console(share.console.Base):

    """Communications to TRS-BTS console."""

    re_blemac = re.compile("[0-9a-f]{12}")  # 'mac' response parser
    # Number of lines in startup banner
    banner_lines = 3
    parameter = share.console.parameter
    cmd_data = {
        "UNLOCK": parameter.Boolean(
            "$DEADBEA7 UNLOCK", writeable=True, readable=False, write_format="{1}"
        ),
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
        "DEBUG": parameter.Boolean(
            "TRS-DBG", writeable=True, readable=False, write_format="{0} {1}"
        ),
        # X-Register values
        "VBATT": parameter.Float("TRS_BTS_AVG_BATT_MV", scale=1000),
        "VPIN": parameter.Float("TRS_BTS_PIN_MV", scale=1000),
        # Calibration commands
        "VBATT_CAL": parameter.Calibration("BATTV", write_expected=1),
        # OverrideTo commands
        "MONITOR": parameter.Override("TRS_BTS_MONITOR_EN_OVERRIDE"),
        "RED_LED": parameter.Override("TRS_BTS_RED_LED_OVERRIDE"),
        "GREEN_LED": parameter.Override("TRS_BTS_GREEN_LED_OVERRIDE"),
        "BLUE_LED": parameter.Override("TRS_BTS_BLUE_LED_OVERRIDE"),
        "BLUETOOTH": parameter.Override("TRS_BTS_BLUETOOTH_EN_OVERRIDE"),
    }
    override_commands = (
        "MONITOR",
        "RED_LED",
        "GREEN_LED",
        "BLUE_LED",
    )

    def initialise(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self.reset_input_buffer()
        self.port.dtr = True  # Pulse RESET using DTR of the BDA4
        time.sleep(0.01)
        self.port.dtr = False
        self.action(None, expected=self.banner_lines)
        self["UNLOCK"] = True
        self["HW_VER"] = hw_ver
        self["SER_ID"] = sernum
        self["NVDEFAULT"] = True
        self["NVWRITE"] = True
        self["DEBUG"] = False  # Suppress debug messages

    def override(self, state=parameter.OverrideTo.NORMAL):
        """Manually override functions of the unit.

        @param state OverrideTo enumeration

        """
        for func in self.override_commands:
            self[func] = state
            time.sleep(0.1)

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
