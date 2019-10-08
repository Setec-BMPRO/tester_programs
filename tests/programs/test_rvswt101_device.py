#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""UnitTest for RVSWT101 device."""

import unittest

import tester
from programs import rvswt101


class RVSWT101Device(unittest.TestCase):

    """RVSWT101 device test suite."""

    # A sample BLE payload
    payload = '1f050112022d624c3a00000300d1139e69'

    def setUp(self):
        """Per-Test setup."""
        self.pkt = rvswt101.device.Packet(self.payload)
        self.rvswt = tester.CANPacket()
        self.rvswt.packet = self.pkt

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

    def test_device(self):
        """Usage of the device directly."""
        for key, value in (
                ('company_id', 1311),
                ('equipment_type', 1),
                ('protocol_ver', 18),
                ('switch_type', 2),
                ('sequence', 25133),
                ('cell_voltage', 3.58176),
                ('signature', 1771967441),
                ):
            self.rvswt.configure(key)
            self.assertEqual(value, self.rvswt.read(None))

    def test_sensor(self):
        """Usage of sensors."""
        sens = tester.sensor.KeyedReading(self.rvswt, 'cell_voltage')
        sens.doc = 'Button cell voltage'
        sens.units = 'Vdc'
        sens.configure()
        sens.opc()
        self.assertEqual((3.58176, ), sens.read())
