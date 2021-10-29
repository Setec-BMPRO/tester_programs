#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""UnitTest for RVSWT101 device."""

import unittest

from programs import rvswt101


class RVSWT101Device(unittest.TestCase):

    """RVSWT101 device test suite."""

    # A sample BLE payload
    payload = '1f050112022d624c3a00000300d1139e69'

    def setUp(self):
        """Per-Test setup."""
        self.pkt = rvswt101.device.Packet(self.payload)

    def test_packet(self):
        """Packet decoder."""
        for prop, value in (
                (self.pkt.company_id, 1311),
                (self.pkt.equipment_type, 1),
                (self.pkt.protocol_ver, 18),
                (self.pkt.switch_type, 2),
                (self.pkt.sequence, 25133),
                (self.pkt.cell_voltage, 3.58176),
                (self.pkt.signature, 1771967441),
                ):
            self.assertEqual(value, prop)
        self.assertEqual(8, len(self.pkt.switches))
