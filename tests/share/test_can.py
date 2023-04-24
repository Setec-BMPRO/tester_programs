#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CAN."""

import unittest

import share


class CAN(unittest.TestCase):

    """CAN test suite."""

    _hdr = 0x18ef4454  # Node to controller packet header

    def test_switchstatuspacket(self):
        """SwitchStatusPacket decoding."""
        pktdata = b"\x00\x00\x40\x00\x00\x00\x00\xa5"
        decoded = {
            "msgtype": 0,
            "swver": 0,
            "pairing": False,
            "retract": False,
            "extend": False,
            "_unused1": False,
            "zone1": False,
            "zone2": False,
            "zone3": False,
            "zone4": True,
            "hex": 0,
            "btnup": False,
            "btndown": False,
            "usb_pwr": False,
            "wake_up": False,
            "_unused2": 0,
            "counter": 0,
            "checksum": 0xa5,
        }
        data = share.can.SwitchStatusDecoder(pktdata)
        self.assertEqual(data.fields, decoded)

    def test_devicestatuspacket(self):
        """DeviceStatusPacket decoding."""
        pktdata = b"\x0a\x00\x00\x00\x00\x00\x00\x00"
        decoded = {
            "msgtype": 10,
            "page": False,
            "sel": False,
            "soft1": False,
            "soft2": False,
            "light1": False,
            "light2": False,
            "light3": False,
            "pump": False,
            "acmain": False,
            "_reserved": 0,
            "backlight": False,
            "menu_state": 0,
            "_unused": 0,
        }
        data = share.can.DeviceStatusDecoder(pktdata)
        self.assertEqual(data.fields, decoded)

    def test_rvmc101controlledbuilder(self):
        """RVMC101ControlLEDBuilder creation."""
        data = b"\x01\x00\x00\xff\xff\xff\x00\x00"
        bld = share.can.RVMC101ControlLEDBuilder()
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)
        bld.pattern = 0x55
        data = b"\x01\x55\x55\xff\xff\xff\x01\xa9"
        self.assertEqual(bld.packet.data, data)

    def test_rvmd50controllcdbuilder(self):
        """RVMD50ControlLCDBuilder creation."""
        data = b"\x10\x00\x00\x00\x00\x00\x00\x00"
        bld = share.can.RVMD50ControlLCDBuilder()
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)
        bld.pattern = 2
        data = b"\x10\x00\x02\x00\x00\x00\x00\x00"
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)

    def test_rvmd50resetbuilder(self):
        """RVMD50ResetBuilder creation."""
        data = b"\x10\x01\x00\x00\x00\x00\x00\x00"
        bld = share.can.RVMD50ResetBuilder()
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)

    def test_rvmd50controlbuttonbuilder(self):
        """RVMD50ControlButtonBuilder creation."""
        data = b"\x10\x02\x00\x00\x00\x00\x00\x00"
        bld = share.can.RVMD50ControlButtonBuilder()
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)
        bld.enable = True
        data = b"\x10\x02\x01\x00\x00\x00\x00\x00"
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)
        bld.button = True
        data = b"\x10\x02\x01\x01\x00\x00\x00\x00"
        self.assertEqual(bld.packet.header.uint, self._hdr)
        self.assertEqual(bld.packet.data, data)
