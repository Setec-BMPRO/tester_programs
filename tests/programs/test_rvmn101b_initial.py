#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMN101B Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvmn101b


class RVMN101BInitial(ProgramTestCase):

    """RVMN101B Initial program test suite."""

    prog_class = rvmn101b.Initial
    parameter = None
    debug = True

    def setUp(self):
        """Per-Test setup."""
        mycan = MagicMock(name='MySerial2CAN')
        mycan.ready_can = False
        mycan.read_can.return_value = True
        patcher = patch(
            'tester.devphysical.can.SerialToCan', return_value=mycan)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.programmer.ARM',
                'share.programmer.Nordic',
                'share.bluetooth.RaspberryBluetooth',
                'programs.rvmn101b.console.Console',
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
                    (sen['SnEntry'], 'A1926040123'),
                    (sen['VBatt'], 12.0),
                    (sen['3V3'], 3.3),
                    ),
                'Initialise': (
                    ),
                'Output': (
                    (sen['HSout'], (0.0, ) + (11.5, 0.0) * 40),
                    (sen['LSout1'], (0.0, 11.5)), (sen['LSout2'], (0.0, 11.5)),
                    ),
                'CanBus': (
                    (sen['MirCAN'], True),
                    ),
                'Bluetooth': (
                    (sen['BleMac'], '112233445566'),
                    (sen['MirScan'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(91, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'PgmARM', 'PgmNordic', 'Initialise', 'Output',
            'CanBus', 'Bluetooth'],
            self.tester.ut_steps)
