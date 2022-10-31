#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2022 SETEC Pty Ltd
"""ODL104 Console driver."""

import re

import share


class Console(share.console.Base):

    """Console via J-Link RTT"""

    cmd_prompt = b"\r\n\x1b[1;32mrtt:~$ \x1b[m".replace(b"\n", b"")
    parameter = share.console.parameter
    cmd_data = {
        "PROD_REV": parameter.String(
            "production product-rev", writeable=True, write_format="{1} {0}"
        ),
        "HW_REV": parameter.String(
            "production hw-rev", writeable=True, write_format="{1} {0}"
        ),
        "SN": parameter.String(
            "production serial", writeable=True, write_format="{1} {0}"
        ),
        "REBOOT": parameter.Boolean(
            "kernel reboot cold", writeable=True, readable=True, write_format="{1}"
        ),
        "MAC": parameter.String("production mac", read_format="{0}"),
        # Keyed reading from the console
        "TANK1": parameter.Float(
            "sensor get tank1", write_format="{0}", read_format="{0}", scale=25
        ),
        "TANK2": parameter.Float(
            "sensor get tank2", write_format="{0}", read_format="{0}", scale=25
        ),
        "TANK3": parameter.Float(
            "sensor get tank3", write_format="{0}", read_format="{0}", scale=25
        ),
        "TANK4": parameter.Float(
            "sensor get tank4", write_format="{0}", read_format="{0}", scale=25
        ),
    }
    # Match the response from the console
    # Sample response:  '\r\nchannel idx=26 distance =   25.000000'
    # Response 25.000000 means 25%
    _tank_regex = re.compile(r".*?(\d+\.\d+).*")

    def brand(self, hw_ver, sernum, banner_lines):
        """Brand the unit with Hardware ID & Serial Number.

        @param hw_ver Tuple (product-rev, hw-rev) ie. ('01A', '01A')
        @param sernum Serial number string
        @param banner_lines Number of startup banner lines

        Startup banner:
        '\n*** ODL104 v1.0.3-0-g8413832 ***\n'
        '\r\n\r\n'
        '\x1b[1;32mrtt:~$ \x1b[m'
        '*** Booting Zephyr OS build zephyr-v2.7.0-59-gc6fe8e97cb9a  ***\n'
        'Reset reason: power-on-reset or a brownout reset'

        Can't flush the banner because the command prompt is in the middle of
        the banner.

        """
        self["PROD_REV"] = hw_ver[0]
        self["HW_REV"] = hw_ver[1]
        self["SN"] = sernum

    def action(self, command=None, delay=0, expected=0):
        """Provide a custom action when reading tanks."""
        response = super().action(command, delay, expected)
        if command.startswith("sensor get tank"):
            found = self._tank_regex.findall(response)
            if found:
                response = found[0]
        return response
