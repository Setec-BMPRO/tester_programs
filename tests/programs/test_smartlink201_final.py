#!/usr/bin/env python3
"""UnitTest for SmartLink201 Final Test program."""

from unittest.mock import patch, Mock

from ..data_feed import UnitTester, ProgramTestCase
from programs import smartlink201


class SmartLink201Final(ProgramTestCase):
    """SmartLink201 Final program test suite."""

    prog_class = smartlink201.Final
    debug = False

    def setUp(self):
        """Per-Test setup."""
        # BLE scanner
        mypi = Mock(name="MyRasPi")
        mypi.scan_advert_blemac.return_value = {"ad_data": "", "rssi": -50}
        patcher = patch("share.bluetooth.RaspberryBluetooth", return_value=mypi)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in ("share.bluetooth.SerialToMAC",):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(1, len(result.readings))
        self.assertEqual(["Bluetooth"], self.tester.ut_steps)
