#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Programmer for Nordic NRF52 devices."""

import pathlib
import os
import subprocess

from . import _base


class NRF52(_base._Base):

    """Nordic Semiconductors programmer using a NRF52."""

    _binary = {
        "nt": pathlib.PureWindowsPath(
            "C:/Program Files/Nordic Semiconductor/nrf5x/bin/nrfjprog.exe"
        ),
        "posix": pathlib.PurePosixPath("nrfjprog"),
    }[os.name]
    # HACK: Force coded RVSWT101 switch code if != 0
    rvswt101_forced_switch_code = 0

    def __init__(self, file, sernum=None):
        """Create a programmer.

        @param file pathlib.Path instance
        @param sernum nRF52 serial number

        """
        super().__init__()
        self._file = file
        self._sernum = sernum

    def program_begin(self):
        """Begin device programming."""
        command = [
            str(self._binary),
            "-f",
            "NRF52",
            "--chiperase",
            "--program",
            str(self._file),
            "--verify",
        ]
        if self._sernum:
            command.extend(["--snr", self._sernum])
        with subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        ) as process:
            result = process.wait(timeout=60)
        # HACK: Force code an RVSWT101 switch code
        if not result and self.rvswt101_forced_switch_code:
            command = [
                self.binary,
                "--memwr",
                "0x70000",
                "--val",
                str(self.rvswt101_forced_switch_code),
            ]
            with subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
            ) as process:
                result = process.wait(timeout=60)
        self.result = result

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()
