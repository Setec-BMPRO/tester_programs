#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""RVMC101 LED Helper."""

import threading

import tester
import share


class LEDControl:

    """Control of the LEDs via CAN."""

    inter_packet_gap = 0.5  # Wait between CAN packets

    def __init__(self, candev):
        """Create instance.

        @param candev CAN interface device

        """
        self.candev = candev
        self._worker = None
        self._evt = threading.Event()

    def __enter__(self):
        """Context Manager entry handler - Override LCD & Backlight.

        @return self

        """
        self._worker = threading.Thread(target=self.worker, name="LEDThread")
        self._worker.start()
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler - Stop sending."""
        self._evt.set()
        self._worker.join()
        self._evt.clear()

    def worker(self):
        """Thread to send a stream of LED_DISPLAY CAN packets."""
        header = tester.devphysical.can.RVCHeader()
        msg = header.message
        msg.DGN = share.can.DGN.RVMC101.value  #  to the RVMC101
        msg.SA = share.can.DeviceID.RVMN101.value  #  from a RVMN101
        data = bytearray([share.can.MessageID.LED_DISPLAY.value])
        data.extend(b"\x00\x00\xff\xff\xff\x00\x00")
        pkt = tester.devphysical.can.CANPacket(header, data)
        # [0]: LED Display = 0x01
        # [1]: LED 7 segment DIGIT0 (LSB, right)
        # [2]: LED 7 segment DIGIT1 (MSB, left)
        # [3.0]: 1 = Enable power to USB (Default)
        # [3.1]: 1 = Stay Awake
        # [3.2-7]: Unused: 0xFC
        # [4-5]: Unused: 0xFF
        # [6]: Sequence number
        # [7]: Checksum
        pattern = 0x01
        while not self._evt.wait(self.inter_packet_gap):
            # Show moving segment on the display
            # The 1st packet we send is ignored due to no previous sequence
            # number. The 2nd+ packets WILL be acted upon.
            pkt.data[1] = pkt.data[2] = pattern
            pattern = 0x01 if pattern == 0x40 else pattern << 1
            pkt.data[6] = (pkt.data[6] + 1) & 0xFF  # Sequence number
            pkt.data[7] = sum(pkt.data[:7]) & 0xFF  # Checksum
            self.candev.send(pkt)
