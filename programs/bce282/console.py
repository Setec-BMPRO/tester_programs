#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BCE282 MSP430 processor console driver."""

import time
import share


class Console(share.console.Base):

    """Communications to BCE282 console."""

    # Console command prompt. Signals the end of output data.
    cmd_prompt = b"\r> "
    # Command suffix between echo of a command and the response.
    res_suffix = b" -> "
    parameter = share.console.parameter
    cmd_data = {
        "ECHO": parameter.Boolean(
            "ECHO", writeable=True, write_format="{0} {1}", read_format="{0}"
        ),
        "UNLOCK": parameter.Boolean(
            "$DEADBEA7 UNLOCK", writeable=True, write_format="{1}"
        ),
        "NV-WRITE": parameter.Boolean(
            "NV-FACTORY-WRITE", writeable=True, write_format="{1}"
        ),
        "RESTART": parameter.Boolean(
            "RESTART", writeable=True, write_format="{1}", write_expected=5
        ),  # 5 lines of startup banner
        "TEST-MODE": parameter.Boolean(
            "TEST-MODE-ENABLE", writeable=True, write_format="{1}"
        ),
        "FL-RELOAD": parameter.Boolean(
            "ADC-FILTER-RELOAD", writeable=True, write_format="{1}"
        ),
        "MSP-STATUS": parameter.Float("NV-STATUS PRINT", read_format="{0}"),
        "MSP-VOUT": parameter.Float("X-SUPPLY-VOLTAGE X@ PRINT", read_format="{0}"),
        "CAL-V": parameter.Float(
            "CAL-VSET", writeable=True, write_format="{0} {1}", read_format="{0}"
        ),
        "PASSWD": parameter.String("BSL-PASSWORD", read_format="{0}"),
    }

    def scaling(self, value):
        """Set scale values for each model."""
        self.cmd_data["MSP-VOUT"].scale = value
        self.cmd_data["CAL-V"].scale = value

    def initialise(self):
        """Setup console for calibration."""
        self["ECHO"] = True
        self["UNLOCK"] = True
        self["NV-WRITE"] = True
        self["RESTART"] = True
        time.sleep(1)
        self["ECHO"] = True
        self["UNLOCK"] = True
        self["TEST-MODE"] = True
        time.sleep(0.1)

    def filter_reload(self):
        """Reset internal filters and wait for readings to settle."""
        self["FL-RELOAD"] = True
        time.sleep(1)

    def action(self, command=None, delay=0.0, expected=0):
        """Send a command, and read the response (force a 0.1s delay).

        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param expected Expected number of responses.
        @return Response (None / String / ListOfStrings).
        @raises console.Error.

        """
        return super().action(command, 0.1, expected)
