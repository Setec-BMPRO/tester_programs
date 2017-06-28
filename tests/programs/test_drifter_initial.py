#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Drifter(BM) Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import drifter


class _DrifterInitial(ProgramTestCase):

    """Drifter(BM) Initial program test suite."""

    prog_class = drifter.Initial

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['pic'].port.flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['oVin'], 12.0), (sen['oVcc'], 3.3),
                    ),
                'CalPre': (
                    (sen['oVsw'], 3.3), (sen['oVref'], 3.3),
                    (sen['o3V3'], -2.7), (sen['o0V8'], -0.8),
                    ),
                'Calibrate': (
                    (sen['oVin'], 12.0), (sen['oIsense'], 0.090),
                    (sen['oVcc'], 3.3),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'CalPre':
                    ('', ) * 2 +
                    ('Banner1\r\nBanner2\r\nBanner3', ) +
                    ('', '0', ''),
                'Calibrate':
                    ('', '-35', '', '', '', ) +
                    ('11950', '', '', '11980', ) +
                    ('-89000', '', '', '-89900', ) +
                    ('', ) +
                    ('20000', '15000', '-8', '160', ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['pic'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(22, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'CalPre','Calibrate'], self.tester.ut_steps)


class Drifter_Initial(_DrifterInitial):

    """Drifter Initial program test suite."""

    parameter = 'STD'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        super()._pass_run()


class DrifterBM_Initial(_DrifterInitial):

    """DrifterBM Initial program test suite."""

    parameter = 'BM'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        super()._pass_run()
