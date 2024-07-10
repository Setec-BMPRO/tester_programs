#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""UnitTest for RVSWT101 device."""

import unittest

from programs import rvswt101


class RVSWT101Device(unittest.TestCase):
    """RVSWT101 device test suite."""

    # A sample BLE payload
    payload = {"255": "1f050112022d624c3a00000300d1139e69"}

    def test_packet(self):
        """Packet decoder."""
        pkt = rvswt101.device.PacketDecoder()
        pkt.decode(
            (
                -75,
                self.payload,
            )
        )
        for prop, value in (
            ("cell_voltage", 3.58176),
            ("company_id", 1311),
            ("equipment_type", 1),
            ("protocol_ver", 18),
            ("rssi", -75),
            ("sequence", 25133),
            ("signature", 1771967441),
            ("switch_code", 8),
            ("switch_type", 2),
        ):
            self.assertEqual(value, pkt.get(prop))
