#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 SETEC Pty Ltd.
"""CAN Packet base classes."""

import abc

import attr
import tester


# Protocol level definitions from the tester module
CANPacket = tester.devphysical.can.CANPacket
RVCHeader = tester.devphysical.can.RVCHeader
SETECHeader = tester.devphysical.can.SETECHeader
SETECMessageType = tester.devphysical.can.SETECMessageType
SETECDataID = tester.devphysical.can.SETECDataID


@attr.s
class DataDecoderMixIn(abc.ABC):  # pylint: disable=too-few-public-methods

    """ABC for all CAN packet data decoders."""

    fields = attr.ib(init=False, factory=dict)

    def decode(self, packet):
        """Decode packet data.

        @param packet CANPacket instance

        """
        self.fields.clear()
        self.worker(packet, self.fields)

    def get(self, name):
        """Access a field value.

        @return Field value, or None for invalid name

        """
        return self.fields.get(name)

    @abc.abstractmethod
    def worker(self, packet, fields):
        """Worker to do the packet decode.

        @param packet CANPacket instance
        @param fields Dictionary to hold decoded field data

        """


class DataDecodeError(Exception):

    """Error decoding a CAN packet."""
