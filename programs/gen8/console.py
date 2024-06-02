#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""GEN8 ARM processor console driver."""

import share


class Console(share.console.Base):
    """Communications to GEN8 console."""

    parameter = share.console.parameter
    cmd_data = {
        "AcFreq": parameter.Float("X-AC-LINE-FREQUENCY", read_format="{0} X?"),
        "AcVolt": parameter.Float("X-AC-LINE-VOLTS", read_format="{0} X?"),
        "5V": parameter.Float("X-RAIL-VOLTAGE-5V", scale=1000, read_format="{0} X?"),
        "12V": parameter.Float("X-RAIL-VOLTAGE-12V", scale=1000, read_format="{0} X?"),
        "24V": parameter.Float("X-RAIL-VOLTAGE-24V", scale=1000, read_format="{0} X?"),
        "SwVer": parameter.String("X-SOFTWARE-VERSION", read_format="{0} X?"),
        "SwBld": parameter.String("X-BUILD-NUMBER", read_format="{0} X?"),
        "CAL_PFC": parameter.Float(
            "CAL-PFC-BUS-VOLTS",
            writeable=True,
            readable=False,
            scale=1000,
            write_format="{0} {1}",
        ),
        "CAL_12V": parameter.Float(
            "CAL-CONVERTER-VOLTS",
            writeable=True,
            readable=False,
            scale=1000,
            write_format="{0} {1}",
        ),
        "UNLOCK": parameter.Boolean(
            "$DEADBEA7 UNLOCK", writeable=True, readable=False, write_format="{1}"
        ),
        "NVWRITE": parameter.Boolean(
            "NV-WRITE", writeable=True, readable=False, write_format="{1}"
        ),
    }
    # Strings to ignore in responses
    ignore = (" ", "Hz", "Vrms", "mV")

    def calpfc(self, voltage):
        """Issue PFC calibration commands.

        @param voltage Measured PFC bus voltage

        """
        self["CAL_PFC"] = voltage
        self["NVWRITE"] = True

    def cal12v(self, voltage):
        """Issue 12V calibration commands.

        @param voltage Measured 12V rail voltage

        """
        self["CAL_12V"] = voltage
        self["NVWRITE"] = True
