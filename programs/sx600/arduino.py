#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""SX-600 Arduino console driver."""

import time

import share


class Arduino(share.console.Base):
    """Communications to Arduino console."""

    cmd_data = {
        "VERSION": share.console.parameter.String("VERSION?", read_format="{0}"),
        "DEBUG": share.console.parameter.String("1 DEBUG", read_format="{0}"),
        "QUIET": share.console.parameter.String("0 DEBUG", read_format="{0}"),
        # 12V OCP commands
        "OCP_MAX": share.console.parameter.String("OCP-MAX", read_format="{0}"),
        "12_OCP_UNLOCK": share.console.parameter.String(
            "OCP-UNLOCK", read_format="{0}"
        ),
        "OCP_STEP_DN": share.console.parameter.String("OCP-STEP-DN", read_format="{0}"),
        "OCP_LOCK": share.console.parameter.String("OCP-LOCK", read_format="{0}"),
        # PFC commands
        "PFC_DN_UNLOCK": share.console.parameter.String(
            "PFC-DN-UNLOCK", read_format="{0}"
        ),
        "PFC_UP_UNLOCK": share.console.parameter.String(
            "PFC-UP-UNLOCK", read_format="{0}"
        ),
        "PFC_STEP_DN": share.console.parameter.String("PFC-STEP-DN", read_format="{0}"),
        "PFC_STEP_UP": share.console.parameter.String("PFC-STEP-UP", read_format="{0}"),
        "PFC_DN_LOCK": share.console.parameter.String("PFC-DN-LOCK", read_format="{0}"),
        "PFC_UP_LOCK": share.console.parameter.String("PFC-UP-LOCK", read_format="{0}"),
    }

    def open(self):
        """Open connection to unit."""
        self.port.open()
        time.sleep(self.open_wait_delay)
        self.port.write(self.cmd_terminator)  # Flush any output junk
        time.sleep(self.open_wait_delay)
        self.reset_input_buffer()  # Flush any input junk
