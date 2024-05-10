#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd
"""BSGateway Test Program."""

import time

import share


class Console(share.console.BadUart):
    """BSGateway console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b">"
    # Console commands
    parameter = share.console.parameter
    cmd_data = {
        # Writable values
        "SET_DAC": parameter.Hex(
            "set_dac",
            writeable=True,
            write_format="{1} 0x{0:04X}",
            readable=False,
            maximum=0xFFFF,
        ),
        "SET_OFF": parameter.Hex(
            "set_off",
            writeable=True,
            write_format="{1} 0x{0:04X}",
            readable=False,
            maximum=0xFFFF,
        ),
        # Action commands
        "CALI": parameter.Hex("cali", read_format="{0}"),
        "EECLR": parameter.String(
            "eeclr", writeable=True, write_format="{1}", readable=False
        ),
        "EEWR": parameter.String(
            "eewr", writeable=True, write_format="{1}", readable=False
        ),
    }

    def open(self):
        """Set parameters and open serial port."""
        self.port.baudrate = 9600
        self.port.timeout = 20
        super().open()

    def reset(self):
        """Micro reset using BDA4 control lines."""
        self.port.dtr = self.port.rts = False
        self.port.dtr = True
        self.port.reset_input_buffer()
        self.port.dtr = False
        time.sleep(1)

    def pre_calibrate(self):
        """Prepare for calibration of the unit."""
        self["SET_DAC"] = 0
        self["SET_OFF"] = 0

    def cali(self):
        """Measure the response to the "cali" command."""
        return self["CALI"]

    def calibrate(self, vcc, offacc, iacc):
        """Apply calibration to the unit.

        @param vcc 3.3V rail voltage
        @param offacc "cali" response with inputs shorted
        @param iacc "cali" response with inputs open

        """
        # Equation lifted verbatim from the Production Notes
        self["SET_DAC"] = round(
            (-(iacc - offacc) * 4095 * 11.77e-6 * 22000) / (vcc * 100 * 16)
        )
        self["SET_OFF"] = offacc
        self["EECLR"] = None
        self["EEWR"] = None
