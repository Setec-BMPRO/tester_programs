#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""RVMC101 LED Helper."""

import threading
import time

import tester


class DisplayControl():

    """Control of the LEDs via CAN."""

    inter_packet_gap = 0.1  # Wait between CAN packets

    def __init__(self, can_dev):
        """Create instance.

        @param can_dev Serial2CAN interface device

        """
        self.serial2can = None
        self._worker = None
        self._evt = threading.Event()

    def __enter__(self, serial2can):
        """Context Manager entry handler - Override LCD & Backlight.

        @return self

        """
        self.serial2can = serial2can
        self._worker = threading.Thread(target=self.worker, name='LEDThread')
        self._worker.start()
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler - Stop sending."""
        self._evt.set()
        self._worker.join()
        self._evt.clear()

    def worker(self):
        """Thread to send a stream of LED_DISPLAY CAN packets."""
        pkt = tester.devphysical.can.RVCPacket()
        msg = pkt.header.message
        msg.priority = 6
        msg.reserved = 0
        msg.DGN = tester.devphysical.can.RVCDGN.setec_led_display.value
        msg.SA = tester.devphysical.can.RVCDeviceID.rvmn101.value
        pkt.data.extend(b'\x01\x7f\x7f\xff\xff\xff\x00\x00')
        # [0]: LED Display = 0x01
        # [1]: LED 7 segment DIGIT0 (LSB, right)
        # [2]: LED 7 segment DIGIT1 (MSB, left)
        # [3.0]: 1 = Enable power to USB (Default)
        # [3.1]: 1 = Stay Awake
        # [3.2-7]: Unused: 0xFC
        # [4-5]: Unused: 0xFF
        # [6]: Sequence number
        # [7]: Checksum
        while not self._evt.is_set():
            # Show "88" on the display (for about 100msec)
            # The 1st packet we send is ignored due to no previous sequence
            # number. The 2nd+ packets WILL be acted upon.
            pkt.data[6] = (pkt.data[6] + 1) & 0xff  # Sequence number
            pkt.data[7] = sum(pkt.data[:7]) & 0xff  # Checksum
            self.serial2can.send('t{0}'.format(pkt))
            time.sleep(self.inter_packet_gap)
