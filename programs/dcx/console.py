#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd.
"""DCX console driver."""

import share


class Console(share.console.BadUart):
    """Console driver."""

    banner_lines = 3
    # "CAN Bound" is STATUS bit 28
    can_bound = 1 << 28
    parameter = share.console.parameter
    cmd_data = {
        # Common commands
        "UNLOCK": parameter.Boolean(
            "$DEADBEA7 UNLOCK", writeable=True, readable=False, write_format="{1}"
        ),
        "RESTART": parameter.Boolean(
            "RESTART", writeable=True, readable=False, write_format="{1}"
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
        "NVDEFAULT": parameter.Boolean(
            "NV-DEFAULT", writeable=True, readable=False, write_format="{1}"
        ),
        "NVWRITE": parameter.Boolean(
            "NV-WRITE", writeable=True, readable=False, write_format="{1}"
        ),
        "NVWIPE": parameter.Boolean(
            "NV-FACTORY-WIPE", writeable=True, readable=False, write_format="{1}"
        ),
        "CAN_PWR_EN": parameter.Boolean("CAN_BUS_POWER_ENABLE", writeable=True),
        "CAN_BIND": parameter.Hex(
            "STATUS", writeable=True, minimum=0, maximum=0xF0000000, mask=can_bound
        ),
        "LOAD_SET": parameter.Float(
            "LOAD_SWITCH_STATE_0",
            writeable=True,
            minimum=0,
            maximum=0x0FFFFFFF,
            scale=1,
        ),
        "BATT_SWITCH": parameter.Boolean("BATTERY_ISOLATE_SWITCH"),
        "BUS_V": parameter.Float("BUS_VOLTS", scale=1000),
        "BATT_V": parameter.Float("BATTERY_VOLTS", scale=1000),
        "BATT_I": parameter.Float("BATTERY_CURRENT", scale=1000),
    }

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        # Add in the 14 load switch current readings
        for i in range(1, 15):
            self.cmd_data["LOAD_{0}".format(i)] = share.console.parameter.Float(
                "LOAD_SWITCH_CURRENT_{0}".format(i), scale=1000
            )

    def brand(self, hw_ver, sernum, reset_relay):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self["NVWIPE"] = True
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self["HW_VER"] = hw_ver
        self["SER_ID"] = sernum
        self["NVWRITE"] = True
        reset_relay.pulse(0.1)  # Reset is required because of HW_VER setting
        self.action(None, delay=1.5, expected=self.banner_lines)

    def load_set(self, set_on=True, loads=()):
        """Set the state of load outputs.

        @param set_on True to set loads ON, False to set OFF.
             ON = 0x01 (Green LED ON, Load ON)
            OFF = 0x10 (Red LED ON, Load OFF)
        @param loads Tuple of loads to set ON or OFF (0-13).

        """
        value = 0x0AAAAAAA if set_on else 0x05555555
        code = 0x1 if set_on else 0x2
        for load in loads:
            if load not in range(14):
                raise ValueError("Load must be 0-13")
            mask = ~(0x3 << (load * 2)) & 0xFFFFFFFF
            bits = code << (load * 2)
            value = value & mask | bits
        self["LOAD_SET"] = value
