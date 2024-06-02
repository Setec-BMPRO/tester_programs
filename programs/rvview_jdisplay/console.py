#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""RvView/JDisplay ARM processor console driver."""

import share


class Console(share.console.BadUart):
    """Base class for a RvView/JDisplay console."""

    # Test mode controlled by STATUS bit 31
    _test_on = 1 << 31
    _test_off = ~_test_on & 0xFFFFFFFF
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
        "STATUS": parameter.Hex(
            "STATUS", writeable=True, minimum=0, maximum=0xF0000000
        ),
        "CAN_BIND": parameter.Hex(
            "STATUS", writeable=True, minimum=0, maximum=0xF0000000, mask=(1 << 28)
        ),
        "CAN": parameter.String("CAN", writeable=True, write_format='"{0} {1}'),
    }

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self.action(None, delay=2.0, expected=2)  # Flush banner
        self["HW_VER"] = hw_ver
        self["SER_ID"] = sernum
        self["NVDEFAULT"] = True
        self["NVWRITE"] = True

    def testmode(self, state):
        """Enable or disable Test Mode.

        In test mode, pushing the button will turn on all display segments
        and the backlight. Pushing the button again turns them all off.

        """
        self._logger.debug("Test Mode = %s", state)
        reply = round(self["STATUS"])
        value = self._test_on | reply if state else self._test_off & reply
        self["STATUS"] = value
