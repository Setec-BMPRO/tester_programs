#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TS3020H Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ts3020h


class TS3020HFinal(ProgramTestCase):

    """TS3020H Final program test suite."""

    prog_class = ts3020h.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FuseCheck': (
                    (sen['oNotifyStart'], True), (sen['o12V'], 0.0),
                    (sen['oYesNoRed'], True), (sen['oNotifyFuse'], True),
                    ),
                'PowerUp': (
                    (sen['o12V'], 13.8), (sen['oYesNoGreen'], True),
                    ),
                'FullLoad': (
                    (sen['o12V'], 13.6),
                    ),
                'OCP': (
                    (sen['o12V'], (13.4, ) * 15 + (13.0, ), ),
                    ),
                'Poweroff': (
                    (sen['oNotifyMains'], True), (sen['o12V'], 0.0),
                    (sen['oYesNoOff'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(11, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['FuseCheck', 'PowerUp', 'FullLoad', 'OCP', 'Poweroff'],
            self.tester.ut_steps)