#!/usr/bin/env python3
"""UnitTest for CAN."""

import unittest

import share


class CAN(unittest.TestCase):

    """CAN test suite."""

    _hdr = 0x18EF4454  # RVMN Node to RVM[CD] controller packet header

    def test_acmonstatusdecoder(self):
        """ACMONStatusDecoder decoding."""
        dec = share.can.ACMONStatusDecoder()
        header = share.can.RVCHeader()
        # ACSTATUS1, 2 legs
        header.message.DGN = share.can.setec_rvc.DGN.ACSTATUS1
        data = b"\x01\xff\xff\xd0\x84\x00\x18\x00"
        packet = share.can.CANPacket(header, data, rvc_mode=True)
        dec.decode(packet)
        data = b"\x81\xff\xff\x08\x84\x00\x1a\x00"
        packet = share.can.CANPacket(header, data, rvc_mode=True)
        dec.decode(packet)
        header.message.DGN = share.can.setec_rvc.DGN.ACSTATUS3
        # ACSTATUS3, 2 legs
        data = b"\x01\xcb\xff\xff\xff\xff\xff\xff"
        packet = share.can.CANPacket(header, data, rvc_mode=True)
        dec.decode(packet)
        data = b"\x81\xcb\xff\xff\xff\xff\xff\xff"
        packet = share.can.CANPacket(header, data, rvc_mode=True)
        dec.decode(packet)
        # Check full dataset
        decoded = {
            "S1L1_current": 100.0,
            "S1L1_fault": 0,
            "S1L1_frequency": 48.0,
            "S1L1_instance": 1,
            "S1L1_iotype": 0,
            "S1L1_leg": 0,
            "S1L1_source": 0,
            "S1L1_voltage": 65535,
            "S1L2_current": 90.0,
            "S1L2_fault": 0,
            "S1L2_frequency": 52.0,
            "S1L2_instance": 1,
            "S1L2_iotype": 0,
            "S1L2_leg": 1,
            "S1L2_source": 0,
            "S1L2_voltage": 65535,
            "S3L1__unused": 3,
            "S3L1_complementary_leg": 255,
            "S3L1_harmonics": 255,
            "S3L1_instance": 1,
            "S3L1_iotype": 0,
            "S3L1_leg": 0,
            "S3L1_phase": 2,
            "S3L1_power_reactive": 65535,
            "S3L1_power_real": 65535,
            "S3L1_source": 0,
            "S3L1_waveform": 3,
            "S3L2__unused": 3,
            "S3L2_complementary_leg": 255,
            "S3L2_harmonics": 255,
            "S3L2_instance": 1,
            "S3L2_iotype": 0,
            "S3L2_leg": 1,
            "S3L2_phase": 2,
            "S3L2_power_reactive": 65535,
            "S3L2_power_real": 65535,
            "S3L2_source": 0,
            "S3L2_waveform": 3,
        }
        self.maxDiff = None
        self.assertEqual(dec.fields, decoded)

    def test_devicestatuspacket(self):
        """DeviceStatusPacket decoding."""
        header = share.can.RVCHeader()
        data = b"\x0a\x00\x00\x00\x00\x00\x00\x00"
        packet = share.can.CANPacket(header, data, rvc_mode=True)
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
        dec = share.can.DeviceStatusDecoder()
        dec.decode(packet)
        self.assertEqual(dec.fields, decoded)

    def test_switchstatuspacket(self):
        """SwitchStatusPacket decoding."""
        header = share.can.RVCHeader()
        data = b"\x00\x00\x40\x00\x00\x00\x00\xa5"
        packet = share.can.CANPacket(header, data, rvc_mode=True)
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
            "checksum": 0xA5,
        }
        dec = share.can.SwitchStatusDecoder()
        dec.decode(packet)
        self.assertEqual(dec.fields, decoded)

    def test_trek2preconditionsbuilder(self):
        """Trek2PreConditionsBuilder creation."""
        hdr = 0x18004069
        data = b"\x00\x00"
        bld = share.can.Trek2PreConditionsBuilder()
        self.assertEqual(bld.packet.header.uint, hdr)
        self.assertEqual(bld.packet.data, data)

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
