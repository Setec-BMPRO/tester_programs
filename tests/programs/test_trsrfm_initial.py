#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRSRFM Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import trsrfm


class TRSRFMInitial(ProgramTestCase):

    """TRSRFM Initial program test suite."""

    prog_class = trsrfm.Initial
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('programs.trsrfm.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        mybt = MagicMock(name='MyBleRadio')
        mybt.scan.return_value = True
        patcher = patch('share.BleRadio', return_value=mybt)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['tstpin_cover'], 0.0), (sen['vin'], 12.0),
                    (sen['3v3'], 3.30),
                    ),
                'TestArm': (
                    (sen['red'], (3.1, 0.5, 3.1)),
                    (sen['green'], (3.1, 0.0, 3.1)),
                    (sen['blue'], (1.6, 0.25, 3.1)),
                    (sen['arm_swver'], trsrfm.initial.Initial.arm_version),
                    (sen['arm_fltcode'], 0),
                    ),
                'Bluetooth': (
                    (sen['btmac'], self.btmac),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(17, len(result.readings))
        self.assertEqual(
            ['Prepare', 'TestArm', 'Bluetooth'], self.tester.ut_steps)
