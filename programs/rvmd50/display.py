#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 LCD & Backlight Helper."""

import time

import attr
import share


@attr.s
class DisplayControl:

    """Control of the LCD & Backlight via CAN."""

    can_dev = attr.ib()
    bld_pattern = attr.ib(init=False, factory=share.can.RVMD50ControlLCDBuilder)
    bld_button = attr.ib(init=False, factory=share.can.RVMD50ControlButtonBuilder)

    def __enter__(self):
        """Context Manager entry handler - Override LCD & Backlight.

        @return self

        """
        self.bld_pattern.pattern = 1  # LCD test pattern to use
        self.bld_button.enable = True
        self.bld_button.button = True
        self._send(self.bld_pattern.packet, self.bld_button.packet)
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler - Release overrides."""
        self.bld_pattern.pattern = 0
        self.bld_button.enable = False
        self.bld_pattern.button = False
        self._send(self.bld_button.packet, self.bld_pattern.packet)

    def _send(self, packet1, packet2):
        """Send CAN Packets with a delay between them."""
        self.can_dev.send(packet1)
        time.sleep(0.1)  # Wait between CAN packets
        self.can_dev.send(packet2)
