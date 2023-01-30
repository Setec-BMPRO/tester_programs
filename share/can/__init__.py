#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""CAN Bus Shared modules for Tester programs."""

import enum


from .setec_rvc import (
    CommandID,
    DeviceID,
    DGN,
    MessageID,
    PacketPropertyReader,
    PacketDetector,
    SwitchStatusPacket,
    DeviceStatusPacket,
    RVMD50ControlButtonPacket,
    RVMD50ControlLCDPacket,
    RVMD50ResetPacket,
    ACMONStatusPacket,
)


__all__ = [
    "CommandID",
    "DeviceID",
    "DGN",
    "MessageID",
    "PacketPropertyReader",
    "PacketDetector",
    "SwitchStatusPacket",
    "DeviceStatusPacket",
    "RVMD50ControlButtonPacket",
    "RVMD50ControlLCDPacket",
    "RVMD50ResetPacket",
    "ACMONStatusPacket",
]


@enum.unique
class SETECDeviceID(enum.IntEnum):

    """CAN Device ID values for different SETEC products.

    Ref:    R_D/Projects/_General/Protocol Specifications/
                SetecCANandBLECommunicationsProtocol Ver2F.pdf

    """

    # pylint: disable=too-few-public-methods
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
