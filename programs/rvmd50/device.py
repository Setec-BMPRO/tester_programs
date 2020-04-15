#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""RVMD50 Packet decoder."""

import ctypes
import struct

import tester


class _ButtonField(ctypes.Structure):

    """RVMD50 button field definition.

    Refer to "RVMN101_5x CAN Specification"

    """

    _fields_ = [
        # Byte D1
        ('page', ctypes.c_uint, 1),
        ('sel', ctypes.c_uint, 1),
        ('soft1', ctypes.c_uint, 1),
        ('soft2', ctypes.c_uint, 1),
        ('light1', ctypes.c_uint, 1),
        ('light2', ctypes.c_uint, 1),
        ('light3', ctypes.c_uint, 1),
        ('pump', ctypes.c_uint, 1),
        # Byte D2
        ('acmain', ctypes.c_uint, 1),
        ('_reserved', ctypes.c_uint, 6),
        ('backlight', ctypes.c_uint, 1),
        ]


class _ButtonRaw(ctypes.Union):

    """Union of the button with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint, 16),
        ('button', _ButtonField),
        ]


class RVMD50Packet():

    """A RVMD50 device status packet."""

    device_status_id = 10

    def __init__(self, packet):
        """Create instance.

        @param packet CAN payload of 8 bytes

        """
        payload = packet.data
        if len(payload) != 8 or payload[0] not in (0, self.device_status_id):
            raise tester.CANPacketDecodeError()
        (   self.msgtype,       # D0
            button_data,        # D1,2
            self.menu_state,    # D3
            _,                  # D4-7
            ) = struct.Struct('<BHBL').unpack(payload)
        # Decode the button data
        button_raw = _ButtonRaw()
        button_raw.uint = button_data
        zss = button_raw.button
        # Assign button data to my properties
        self.page = bool(zss.page)
        self.sel = bool(zss.sel)
        self.soft1 = bool(zss.soft1)
        self.soft2 = bool(zss.soft2)
        self.light1 = bool(zss.light1)
        self.light2 = bool(zss.light2)
        self.light3 = bool(zss.light3)
        self.pump = bool(zss.pump)
        self.acmain = bool(zss.acmain)
        self.backlight = bool(zss.backlight)


def display_test_pattern(serial2can, pattern):
    """Send a RVMD50 test pattern control packet."""
    if pattern not in range(4):
        raise ValueError('Test pattern must be 0-3')
    pkt = tester.devphysical.can.RVCPacket()
    msg = pkt.header.message
    msg.priority = 6
    msg.reserved = 0
    msg.DGN = tester.devphysical.can.RVCDGN.setec_rvmd50.value
    msg.SA = tester.devphysical.can.RVCDeviceID.rvmn5x.value
    pkt.data.extend(b'\x10\x00')                # Cmd 16, Cmd ID 0
    pkt.data.extend(bytes([pattern & 0xff]))    # Pattern number
    pkt.data.extend(b'\xff\xff\xff\xff\xff')    # Padding
    serial2can.send('t{0}'.format(pkt))
