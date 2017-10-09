#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BatteryCheck Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import batterycheck


class BatteryCheckInitial(ProgramTestCase):

    """BatteryCheck Initial program test suite."""

    prog_class = batterycheck.Initial
    parameter = None
    debug = False
    serial = 'A1509020010'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('share.ProgramARM')
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('subprocess.check_output')  # for step ProgramAVR
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('programs.batterycheck.console.Console')
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('share.BtRadio', new=self._makebt)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _makebt(self, x):
        mybt = MagicMock(name='MyBtRadio')
        mybt.scan.return_value = True
        return mybt

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PreProgram':(
                    (sen['oSnEntry'], (self.serial, )),
                    (sen['reg5V'], 5.10),
                    (sen['reg12V'], 12.00),
                    (sen['o3V3'], 3.30),
                    ),
                'ARM': (
                    (sen['relay'], 5.0),
                    (sen['shunt'], 62.5 / 1250),
                    (sen['ARMcurr'], -62.0),
                    (sen['ARMsoft'], batterycheck.initial.Initial.arm_version),
                    (sen['ARMvolt'], 12.12),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(12, len(result.readings))
        self.assertEqual(
            ['PreProgram', 'ProgramAVR', 'ProgramARM',
             'InitialiseARM', 'ARM', 'BlueTooth'],
            self.tester.ut_steps)
