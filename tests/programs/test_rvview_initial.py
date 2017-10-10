#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVVIEW Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import rvview


class RvViewInitial(ProgramTestCase):

    """RVVIEW Initial program test suite."""

    prog_class = rvview.Initial
    parameter = None
    debug = False
    sernum = 'A1626010123'

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('share.ProgramARM')
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch(
            'programs.rvview.console.DirectConsole', new=self._makecon)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('programs.rvview.console.TunnelConsole')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _makecon(self, _):
        mycon = MagicMock(name='MyConsole')
        mycon.port.readline.return_value = b'RRQ,32,0'
        return mycon

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['oSnEntry'], (self.sernum, )),
                    (sen['oVin'], 7.5),
                    (sen['o3V3'], 3.3),
                    ),
                'Initialise': (
                    (sen['oSwVer'], (rvview.Initial.bin_version, )),
                    ),
                'Display': (
                    (sen['oYesNoOn'], True),
                    (sen['oYesNoOff'], True),
                    (sen['oBkLght'], (3.0, 0.0)),
                    ),
                'CanBus': (
                    (sen['arm_canbind'], 1 << 28),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(10, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'Initialise', 'Display', 'CanBus'],
            self.tester.ut_steps)
