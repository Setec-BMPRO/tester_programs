#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Initial Test program."""

from unittest.mock import MagicMock, patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvswt101


class RVSWT101Initial(ProgramTestCase):

    """RVSWT101 Initial program test suite."""

    prog_class = rvswt101.Initial
    per_panel = 10
    parameter = '4gp1'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        mycon = MagicMock(name='MyConsole')
        mycon.get_mac.return_value = '001ec030c2be'
        patcher = patch(
            'programs.rvswt101.console.Console', return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.programmer.Nordic',
                'share.bluetooth.RaspberryBluetooth',
                'programs.rvswt101.config.SerialToMAC',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['SnEntry'], 'A1526040123'),
                    (sen['vin'], 3.3),
                    ),
                'ProgramTest': (
                    (sen['mirmac'], 'ec70225e3dba'),
                    (sen['mirscan'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(
            tuple('UUT{0}'.format(uut)
                for uut in range(1, self.per_panel + 1)))
        for res in self.tester.ut_result:
            self.assertEqual('P', res.code)
            self.assertEqual(4, len(res.readings))
        self.assertEqual(
            ['PowerUp', 'ProgramTest'],
            self.tester.ut_steps)
