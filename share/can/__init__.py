#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""CAN Bus Shared modules for Tester programs."""

import contextlib

import attr
import tester

from . import _base
from .setec_can import (
    PreConditionsBuilder,
    SETECDeviceID,
)
from .setec_rvc import (
    # Packet generators
    RVMC101ControlLEDBuilder,
    RVMD50ControlButtonBuilder,
    RVMD50ControlLCDBuilder,
    RVMD50ResetBuilder,
    # Packet data decoders
    ACMONStatusDecoder,
    DeviceStatusDecoder,
    SwitchStatusDecoder,
)


__all__ = [
    # SETEC custom data
    "SETECDeviceID",
    # Sensors
    "PacketPropertyReader",
    "PacketDetector",
    # Packet generators
    "PreConditionsBuilder",
    "RVMC101ControlLEDBuilder",
    "RVMD50ControlButtonBuilder",
    "RVMD50ControlLCDBuilder",
    "RVMD50ResetBuilder",
    # Packet data decoders
    "ACMONStatusDecoder",
    "DeviceStatusDecoder",
    "SwitchStatusDecoder",
]


@attr.s
class PacketPropertyReader:

    """Custom logical instrument to read CAN packet properties."""

    canreader = attr.ib()  # tester.CANReader instance
    decoder = attr.ib()  # CAN packet data decoder instance
    _read_key = attr.ib(init=False, default=None)

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def opc(self):
        """Sensor: OPC."""

    def read(self, callerid):  # pylint: disable=unused-argument
        """Sensor: Read payload data using the last configured key.

        @param callerid Identity of caller
        @return Packet property value, or None

        """
        try:
            packet = self.canreader.read()
            data = self.decoder.decode(packet.data)
        except tester.CANReaderError:  # A timeout due to no traffic
            return None
        except _base.DataDecodeError:  # Probably incorrect packet type
            return None
        return data.fields[self._read_key]


@attr.s
class PacketDetector:

    """Custom logical instrument to detect CAN packet traffic."""

    canreader = attr.ib()  # tester.CANReader instance

    def configure(self, key):  # pylint: disable=unused-argument
        """Sensor: Configure for next reading."""

    def opc(self):
        """Sensor: OPC."""

    def read(self, callerid):  # pylint: disable=unused-argument
        """Sensor: Read presence of CAN traffic.

        @param callerid Identity of caller
        @return True if CAN traffic is seen

        """
        result = False
        with contextlib.suppress(tester.CANReaderError):
            self.canreader.read()
            result = True
        return result
