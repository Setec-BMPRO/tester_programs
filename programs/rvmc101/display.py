#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""RVMC101 LED Helper."""

import threading

from attrs import define, field

import share


@define
class LEDControl:

    """Control of the LEDs via CAN."""

    candev = field()
    _worker = field(init=False, default=None)
    _evt = field(init=False, factory=threading.Event)
    inter_packet_gap = 0.5  # Wait between CAN packets

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
        builder = share.can.RVMC101ControlLEDBuilder()
        pattern = 0x01
        while not self._evt.wait(self.inter_packet_gap):
            # Show moving segment on the display
            # The 1st packet we send is ignored due to no previous sequence
            # number. The 2nd+ packets WILL be acted upon.
            builder.pattern = pattern
            self.candev.send(builder.packet)
            pattern = 0x01 if pattern == 0x40 else pattern << 1
