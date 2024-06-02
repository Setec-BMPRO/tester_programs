#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 LCD & Backlight Helper."""

import time

from attrs import define, field
import share


@define
class DisplayControl:
    """Control of the LCD & Backlight via CAN."""

    can_dev = field()
    bld_pattern = field(init=False, factory=share.can.RVMD50ControlLCDBuilder)
    bld_button = field(init=False, factory=share.can.RVMD50ControlButtonBuilder)

    def __enter__(self):
        """Context Manager entry handler - Override LCD & Backlight.

        @return self

        """
        self.bld_pattern.pattern = 1  # LCD test pattern to use
        self.can_dev.send(self.bld_pattern.packet)
        time.sleep(0.1)  # Wait between CAN packets
        self.bld_button.enable = True
        self.bld_button.button = True
        self.can_dev.send(self.bld_button.packet)
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler - Release overrides."""
        self.bld_button.enable = False
        self.bld_button.button = False
        self.can_dev.send(self.bld_button.packet)
        time.sleep(0.1)  # Wait between CAN packets
        self.bld_pattern.pattern = 0
        self.can_dev.send(self.bld_pattern.packet)
