#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""BLExtender/SmartLink201 Test Program."""

import re

import share


def tank_name(index):
    """Generate a Tank input name.

    @parm index Tank input index (0-15)
    @return Tank name string eg: "TANK1-1" to "TANK4-4"

    """
    return "TANK{0}-{1}".format((index // 4) + 1, (index % 4) + 1)


class _Console(share.console.Base):
    """BLExtender/SmartLink201 base console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b"uart:~$ \x1b[m"
    ignore = ("\x1b[m", "\x1b[1;31m", "\x1b[1;32m")

    def reset(self):
        """RESET using the BDA4."""
        self.port.dtr = True  # Pulse RESET using DTR of the BDA4
        self.port.reset_input_buffer()
        self.port.dtr = False

    def initialise(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '02A'
        @param hardware_rev Hardware revision from ECO eg: '02A'

        """
        self["SERIAL"] = sernum
        self["PRODUCT-REV"] = product_rev
        self["HARDWARE-REV"] = hardware_rev


class BLExtenderConsole(_Console):
    """BLExtender console."""

    banner_lines = 11  # Startup banner lines
    # Console commands
    parameter = share.console.parameter
    cmd_data = {
        # Writable values
        "SERIAL": parameter.String(
            "setec serial", writeable=True, write_format="{1} {0}"
        ),
        "PRODUCT-REV": parameter.String(
            "setec product-rev", writeable=True, write_format="{1} {0}"
        ),
        "HARDWARE-REV": parameter.String(
            "setec hw-rev", writeable=True, write_format="{1} {0}"
        ),
        # Action commands
        "REBOOT": parameter.String(
            "kernel reboot cold",
            writeable=True,
            write_format="{1}",
            write_expected=banner_lines,
        ),
        # Readable values
        "SW_VER": parameter.String("setec sw-rev", read_format="{0}"),
        "MAC": parameter.String("setec mac", read_format="{0}"),
    }

    def initialise(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '02A'
        @param hardware_rev Hardware revision from ECO eg: '02A'

        """
        self.reset()
        self.action(None, expected=self.banner_lines)
        super().initialise(sernum, product_rev, hardware_rev)


class SmartLink201Console(_Console):
    """SmartLink201 console."""

    banner_lines = 12  # Startup banner lines
    # Console commands
    parameter = share.console.parameter
    vbatt_key = "BATT"  # Key to read Vbatt
    cmd_data = {
        # Writable values
        "SERIAL": parameter.String(
            "smartlink serial", writeable=True, write_format="{1} {0}"
        ),
        "PRODUCT-REV": parameter.String(
            "smartlink product-rev", writeable=True, write_format="{1} {0}"
        ),
        "HARDWARE-REV": parameter.String(
            "smartlink hw-rev", writeable=True, write_format="{1} {0}"
        ),
        "BATT_CAL": parameter.Float(
            "smartlink battery calibrate",
            scale=1000,
            writeable=True,
            write_format="{1} {0}",
        ),
        # Action commands
        "REBOOT": parameter.String(
            "kernel reboot cold",
            writeable=True,
            write_format="{1}",
            write_expected=banner_lines,
        ),
        # Readable values
        "SW_VER": parameter.String("smartlink sw-rev", read_format="{0}"),
        "MAC": parameter.String("smartlink mac", read_format="{0}"),
        vbatt_key: parameter.String("smartlink battery read", read_format="{0}"),
    }
    # Storage of response to analog query command
    analog_linecount = 18
    analog_regexp = re.compile(r"^([0-9]{1,2})\:(0x[0-9A-F]{4})$")
    analog_data = {}  # Analog readings
    vbatt_read_wait = 6.0  # Delay until Vbatt reading is valid

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        # Background timer for Vbatt reading readiness
        self.vbatttimer = share.BackgroundTimer(self.vbatt_read_wait)

    def __getitem__(self, key):
        """Read a value."""
        if key in self.analog_data:  # Try an analog value
            return self.analog_data[key]
        if key == self.vbatt_key:  # Wait for Vbatt reading
            self.vbatttimer.wait()
        return super().__getitem__(key)  # Try the command table

    def initialise(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '02A'
        @param hardware_rev Hardware revision from ECO eg: '02A'

        """
        self.reset()
        self.action(None, expected=self.banner_lines)
        self.vbatttimer.start()
        super().initialise(sernum, product_rev, hardware_rev)

    def vbatt_cal(self, vbatt):
        """Calibrate Vbatt reading.

        @param vbatt Vbatt actual input value in mV

        """
        self["BATT_CAL"] = vbatt
        self["REBOOT"] = None
        self.vbatttimer.start()

    def analog_read(self):
        """Read analog input raw values."""
        self.analog_data.clear()
        response = self.action("smartlink analog", expected=self.analog_linecount)
        # Response lines are <DecimalIndex>:<HexValue> eg "9:0x0FFF"
        for line in response:
            match = self.analog_regexp.match(line)
            if match:
                index, hex = match.groups()
                name = tank_name(int(index))
                self.analog_data[name] = int(hex, 16)
