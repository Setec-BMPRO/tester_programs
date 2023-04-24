#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""CAN Bus Shared modules for Tester programs."""

import contextlib
import enum

import attr
import tester


from .setec_rvc import (
    # Packet generators
    RVMC101ControlLEDBuilder,
    RVMD50ControlButtonBuilder,
    RVMD50ControlLCDBuilder,
    RVMD50ResetBuilder,
    # Packet data decoders
    PacketDecodeError,
    ACMONStatusDecoder,
    DeviceStatusDecoder,
    SwitchStatusDecoder,
)


__all__ = [
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


@enum.unique
class SETECDeviceID(enum.IntEnum):  # pylint: disable=too-few-public-methods

    """CAN Device ID values for different SETEC products.

    Reference:
        R_D/Projects/_General/Protocol Specifications/
            SetecCANandBLECommunicationsProtocol Ver2F.pdf

    """

    CN100 = 4
    BP35 = 16
    J35 = 20
    TREK2 = 32
    CN101 = 36
    BLE2CAN = 40
    RVVIEW = 44
    BC2 = 128
    CAN_AP = 16384
    GENERIC = 16400


@attr.s
class PreConditionsBuilder:  # pylint: disable=too-few-public-methods

    """A TREK2 PreConditions packet builder."""

    packet = attr.ib(init=False)

    @packet.default
    def _packet_default(self):
        """Build a Preconditions packet (for Trek2)."""
        header = tester.devphysical.can.SETECHeader()
        msg = header.message
        msg.device_id = SETECDeviceID.BP35.value
        msg.msg_type = tester.devphysical.can.SETECMessageType.ANNOUNCE.value
        msg.data_id = tester.devphysical.can.SETECDataID.PRECONDITIONS.value
        data = b"\x00\x00"  # Dummy data
        return tester.devphysical.can.CANPacket(header, data)


@attr.s
class PacketPropertyReader:

    """Custom logical instrument to read CAN packet properties."""

    canreader = attr.ib()  # tester.CANReader instance
    decoder = attr.ib()  # CAN packet data decoder class
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
            data = self.decoder(packet.data)
        except tester.CANReaderError:  # A timeout due to no traffic
            return None
        except PacketDecodeError:  # Probably incorrect packet type
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
