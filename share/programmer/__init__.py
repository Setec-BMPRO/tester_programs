#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd.
"""Programmer Drivers."""

import pathlib

from attrs import define

from ._base import VerificationError
from .arm import ARM
from .avr import AVR

__all__ = [
    "VerificationError",
    "ARM",
    "AVR",
]


@define
class JFlashProject:
    """Common store of JFlash project files for devices."""

    @classmethod
    def projectfile(cls, device: str) -> pathlib.Path:
        """Path to a device's jflash project file.

        @param device Device name string (Matches project filename)
        @return Path to device project file

        """
        return pathlib.Path(__file__) / "programmer" / (device + ".jflash")
