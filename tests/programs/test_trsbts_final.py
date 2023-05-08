#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS-BTS Final Test program."""

from unittest.mock import patch, Mock

from ..data_feed import UnitTester, ProgramTestCase
from programs import trsbts


class TRSBTSFinal(ProgramTestCase):

    """TRS-BTS Final program test suite."""

    prog_class = trsbts.Final
    parameter = "BTS"
    debug = False
    btmac = "001ec030bc15"

    def setUp(self):
        """Per-Test setup."""
        # Serial number to BLE MAC lookup
        mysm = Mock(name="MySerMac")
        mysm.blemac_get.return_value = self.btmac
        patcher = patch("share.bluetooth.SerialToMAC", return_value=mysm)
        self.addCleanup(patcher.stop)
        patcher.start()
        # BLE scanner
        mypi = Mock(name="MyRasPi")
        mypi.scan_advert_blemac.return_value = {"ad_data": "", "rssi": -50}
        patcher = patch("share.bluetooth.RaspberryBluetooth", return_value=mypi)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Pin": (
                    (sen["sernum"], "A2026040123"),
                    (sen["vbat"], 12.0),
                    (sen["brake"], (12.0, 0.1)),
                    (sen["pin_in"], True),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(8, len(result.readings))
        self.assertEqual(["Pin", "Bluetooth"], self.tester.ut_steps)
