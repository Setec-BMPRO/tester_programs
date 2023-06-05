#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Programmer for NXP ARM devices."""

import threading
import time

import isplpc
import serial

from . import _base


class ARM(_base._Base):

    """ARM programmer using the isplpc package."""

    def __init__(
        self,
        port,
        file,
        crpmode=None,
        boot_relay=None,
        reset_relay=None,
        bda4_signals=False,
    ):
        """Create a programmer.

        @param port Serial port to use
        @param file pathlib.Path instance
        @param crpmode Code Protection:
                        True: ON, False: OFF, None: per 'bindata'
        @param boot_relay Relay device to assert BOOT to the ARM
        @param reset_relay Relay device to assert RESET to the ARM
        @param bda4_signals True: Use BDA4 serial lines for RESET & BOOT

        """
        super().__init__()
        self.port = port
        self.file = file
        self.boot_relay = boot_relay
        self.reset_relay = reset_relay
        self.bda4_signals = bda4_signals
        self.baudrate = 115200
        self.crpmode = crpmode
        self._bindata = None
        self._ser = None
        self._worker = None

    def program_begin(self):
        """Begin programming a device.

        If BOOT or RESET relay devices are available, use them to put the chip
        into bootloader mode (Assert BOOT, pulse RESET).
        BDA4 serial signals: RTS = BOOT, DTR = RESET.

        """
        # Read the image & open serial port on main thread
        if not self._bindata:
            with self.file.open("rb") as infile:
                self._bindata = bytearray(infile.read())
        self._ser = serial.Serial(port=self.port, baudrate=self.baudrate)
        # We need to wait just a little before flushing the port
        time.sleep(0.5)
        self._ser.reset_input_buffer()
        # Device I/O activity is only done on main thread
        if self.bda4_signals:
            self._ser.rts = self._ser.dtr = True  # Assert BOOT & RESET
            time.sleep(0.01)
            self._ser.dtr = False  # Release RESET
            time.sleep(0.01)
            self._ser.rts = False  # Release BOOT
        else:
            if self.boot_relay:
                self.boot_relay.set_on()  # Assert BOOT
            if self.reset_relay:
                self.reset_relay.pulse(0.1)  # Pulse RESET
            if self.boot_relay:
                self.boot_relay.set_off()  # Release BOOT
        # Target device is now running in ISP mode
        pgm = isplpc.Programmer(
            self._ser,
            self._bindata,
            erase_only=False,
            verify=False,
            crpmode=self.crpmode,
        )
        self._worker = threading.Thread(
            target=self.worker, name="ARMthread", args=(pgm,)
        )
        self._worker.start()

    def worker(self, pgm):
        """Worker thread to do the programming.

        @param pgm islpc.Programmer instance

        """
        result = self.pass_result
        try:
            pgm.program()
        except Exception as exc:  # pylint: disable=broad-except
            result = str(exc)
        self.result = result

    def program_wait(self):
        """Wait for device programming to finish."""
        self._worker.join()
        self._ser.close()
        self._ser = None
        self.result_check()
