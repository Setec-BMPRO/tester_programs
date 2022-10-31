#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""SamB11 device Base console driver.

The UART does have an 8-byte buffer, but the console task runs at a lower
priority, so it can still drop characters of the longer command strings.
Thus, use the BadUart protocol.

"""

from . import parameter
from . import protocol


class SamB11(protocol.BadUart):

    """Communications to SamB11 based console."""

    # Number of lines in startup banner
    banner_lines = 3
    # Common commands
    common_commands = {
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
    }

    def __init__(self, port):
        """Add common commands into cmd_data.

        @param port Serial instance to use

        """
        super().__init__(port)
        for key, command in self.common_commands.items():
            self.cmd_data[key] = command
        self.override_commands = ()

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

    def override(self, state=parameter.OverrideTo.NORMAL):
        """Manually override functions of the unit.

        @param state OverrideTo enumeration

        """
        for func in self.override_commands:
            self[func] = state
