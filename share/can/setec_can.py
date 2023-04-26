#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd
"""SETEC custom CAN Packet decoders & builders.

Reference:
    R_D/Projects/_General/Protocol Specifications/
        SetecCANandBLECommunicationsProtocol Ver2F.pdf

"""

import enum

import attr

from . import _base


@enum.unique
class SETECDeviceID(enum.IntEnum):  # pylint: disable=too-few-public-methods

    """CAN Device ID values for different SETEC products."""

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
class Trek2PreConditionsBuilder:  # pylint: disable=too-few-public-methods

    """A TREK2 PreConditions packet builder."""

    packet = attr.ib(init=False)

    @packet.default
    def _packet_default(self):
        """Build a Preconditions packet."""
        header = _base.SETECHeader()
        msg = header.message
        msg.device_id = SETECDeviceID.BP35.value
        msg.msg_type = _base.SETECMessageType.ANNOUNCE.value
        msg.data_id = _base.SETECDataID.PRECONDITIONS.value
        data = b"\x00\x00"  # Dummy data
        return _base.CANPacket(header, data)


@attr.s
class RvviewTestModeBuilder:  # pylint: disable=too-few-public-methods

    """A RVVIEW TestMode packet builder."""

    packet = attr.ib(init=False)

    @packet.default
    def _packet_default(self):
        """Build a TestMode packet."""
        header = _base.SETECHeader()
        msg = header.message
        msg.device_id = SETECDeviceID.RVVIEW.value
        msg.msg_type = _base.SETECMessageType.COMMAND.value
        msg.data_id = _base.SETECDataID.XREG.value
        data = b"\xC5"  # XReg 0xC5 toggles testmode
        return _base.CANPacket(header, data)
