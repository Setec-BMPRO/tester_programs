#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""RVMD50 LCD & Backlight Helper."""

import time

import share


class DisplayControl():

    """Control of the LCD & Backlight via CAN."""

    test_pattern = 1        # LCD test pattern to use
    inter_packet_gap = 0.1  # Wait between CAN packets

    def __init__(self, can_dev):
        """Create instance.

        @param can_dev CAN interface device

        """
        self.pkt_pattern = share.can.RVMD50ControlLCDPacket(can_dev)
        self.pkt_button = share.can.RVMD50ControlButtonPacket(can_dev)

    def __enter__(self):
        """Context Manager entry handler - Override LCD & Backlight.

        @return self

        """
        self.pkt_pattern.pattern = self.test_pattern
        self.pkt_pattern.send()
        time.sleep(self.inter_packet_gap)
        self.pkt_button.enable = self.pkt_button.button = True
        self.pkt_button.send()
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler - Release overrides."""
        self.pkt_button.enable = self.pkt_pattern.button = False
        self.pkt_button.send()
        time.sleep(self.inter_packet_gap)
        self.pkt_pattern.pattern = 0
        self.pkt_pattern.send()
