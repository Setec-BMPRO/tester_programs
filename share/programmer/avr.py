#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""Programmer for AVR UPDI devices."""

import updi

from . import _base


class AVR(_base._Base):

    """AVR programmer using the updi package."""

    def __init__(self, port, file, baudrate=115200, device="tiny406", fuses=None):
        """Create a programmer.

        @param port Serial port name to use
        @param file pathlib.Path instance
        @param baudrate Serial baudrate
        @param device Device type
        @param fuses Device fuse settings
            Dictionary{FuseName: (FuseNumber, FuseValue)}

        """
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._file = file
        self._device = updi.Device(device)
        self._fuses = fuses if fuses else {}

    def program_begin(self):
        """Program a device."""
        try:
            nvm = updi.UpdiNvmProgrammer(
                comport=self._port, baud=self._baudrate, device=self._device
            )
            try:
                nvm.enter_progmode()
            except updi.UpdiError:
                nvm.unlock_device()
            nvm.get_device_info()
            data, start_address = nvm.load_ihex(str(self._file))
            nvm.chip_erase()
            nvm.write_flash(start_address, data)
            readback = nvm.read_flash(nvm.device.flash_start, len(data))
            for offset, value in enumerate(data):
                if value != readback[offset]:
                    raise _base.VerificationError("Verify error at 0x{0:04X}".format(offset))
            for fuse_num, fuse_val in self._fuses.values():
                nvm.write_fuse(fuse_num, fuse_val)
            nvm.leave_progmode()
            self.result = self.pass_result
        except updi.UpdiError as exc:
            self.result = str(exc)

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()
