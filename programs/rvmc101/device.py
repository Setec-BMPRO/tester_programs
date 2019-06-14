#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101 Packet decoder."""

import ctypes
import struct


class PacketDecodeError(Exception):

    """Error decoding RVMC101 status packet."""


class _SwitchField(ctypes.Structure):

    """RVMC switch field definition.

    Refer to "RVM101 CAN Specification"

    """

    _fields_ = [
        ('_pairing', ctypes.c_uint, 2),
        ('retract', ctypes.c_uint, 2),
        ('extend', ctypes.c_uint, 2),
        ('_unused1', ctypes.c_uint, 2),
        ('zone1', ctypes.c_uint, 2),
        ('zone2', ctypes.c_uint, 2),
        ('zone3', ctypes.c_uint, 2),
        ('zone4', ctypes.c_uint, 2),
        ('_hex', ctypes.c_uint, 4),
        ('up', ctypes.c_uint, 2),
        ('down', ctypes.c_uint, 2),
        ('usb_pwr', ctypes.c_uint, 1),
        ('wake_up', ctypes.c_uint, 1),
        ('_unused2', ctypes.c_uint, 6),
        ]


class _SwitchRaw(ctypes.Union):

    """Union of the RVMC switch type with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint),
        ('switch', _SwitchField),
        ]


class Packet():

    """A RVMC101 broadcast packet."""

    switch_status = 0

    def __init__(self, packet):
        """Create instance.

        @param packet CANPacket instance

        """
        payload = packet.data
        if len(payload) != 8 or payload[0] != self.switch_status:
            raise PacketDecodeError()
        (   self.msgtype,
            switch_data,
            self.swver,
            self.counter,
            self.checksum,
            ) = struct.Struct('<BLB3').unpack(payload)
        # Decode the switch data
        switch_raw = _SwitchRaw()
        switch_raw.uint = switch_data
        zss = switch_raw.switch
        # Assign switch data to my properties
        self.retract = bool(zss.retract)
        self.extend = bool(zss.extend)
        self.zone1 = bool(zss.zone1)
        self.zone2 = bool(zss.zone2)
        self.zone3 = bool(zss.zone3)
        self.zone4 = bool(zss.zone4)
        self.up = bool(zss.up)
        self.down = bool(zss.down)
        self.usb_pwr = bool(zss.usb_pwr)
        self.wake_up = bool(zss.wake_up)
