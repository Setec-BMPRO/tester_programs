#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101 Packet decoder."""

import ctypes
import struct

import tester


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


class RVMC101Packet():

    """A RVMC101 broadcast packet."""

    switch_status = 0

    def __init__(self, packet):
        """Create instance.

        @param packet CAN payload of 8 bytes

        """
        payload = packet.data
        if len(payload) != 8 or payload[0] != self.switch_status:
            raise tester.CANPacketDecodeError()
        (   self.msgtype,
            switch_data,
            self.swver,
            self.counter,
            self.checksum,
            ) = struct.Struct('<BL3B').unpack(payload)
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


# This is how to send Display Control packets
#    def send_led_display(serial2can):
#        """Send a LED_DISPLAY packet."""
#        pkt = tester.devphysical.can.RVCPacket()
#        msg = pkt.header.message
#        msg.priority = 6
#        msg.reserved = 0
#        msg.DGN = tester.devphysical.can.RVCDGN.setec_led_display.value
#        msg.SA = tester.devphysical.can.RVCDeviceID.rvmn101.value
#        sequence = 1
#        # Show "88" on the display (for about 100msec)
#        # The 1st packet we send is ignored due to no previous sequence number
#        pkt.data.extend(b'\x01\xff\xff\xff\xff\xff')
#        pkt.data.extend(bytes([sequence & 0xff]))
#        pkt.data.extend(bytes([sum(pkt.data) & 0xff]))
#        serial2can.send('t{0}'.format(pkt))
#        sequence += 1
#        # The 2nd packet WILL be acted upon
#        pkt.data.clear()
#        pkt.data.extend(b'\x01\xFF\xFF\xFF\xFF\xFF')
#        pkt.data.extend(bytes([sequence & 0xff]))
#        pkt.data.extend(bytes([sum(pkt.data) & 0xff]))
#        serial2can.send('t{0}'.format(pkt))
#        sequence += 1
