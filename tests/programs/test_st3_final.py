#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for STxx-III Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import st3


class _STxxIIIFinal(ProgramTestCase):

    """STxx-III Final program base test suite."""

    prog_class = st3.Final
    parameter = None

    def _pass_run(self, barcode):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FuseLabel': (
                    (sen['oBarcode'], (barcode, )),
                    ),
                'PowerUp': (
                    (sen['oLoad'], 14.0),
                    (sen['oFuse1'], 13.65), (sen['oFuse2'], 13.65),
                    (sen['oFuse3'], 13.65), (sen['oFuse4'], 13.65),
                    (sen['oFuse5'], 13.65), (sen['oFuse6'], 13.65),
                    (sen['oFuse7'], 13.65), (sen['oFuse8'], 13.65),
                    (sen['oBatt'], 13.65), (sen['oYesNoOrGr'], True),
                    ),
                'Battery': (
                    (sen['oBatt'], (0.4, 13.65)), (sen['oYesNoRedOn'], True),
                    (sen['oYesNoRedOff'], True),
                    ),
                'LoadOCP': (
                    (sen['oLoad'], (13.5, ) * 15 + (11.0, 0.5, 13.6), ),
                    ),
                'BattOCP': (
                    (sen['oBatt'], (13.5, ) * 12 + (11.0, 13.6, ), ),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(21, len(result.readings))
        self.assertEqual(
            ['FuseLabel', 'PowerUp', 'Battery', 'LoadOCP', 'BattOCP'],
            self.tester.ut_steps)


class ST20_III_Final(_STxxIIIFinal):

    """ST20-III Final program test suite."""

    parameter = '20'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        super()._pass_run('ST20-III')


class ST35_III_Final(_STxxIIIFinal):

    """ST35-III Final program test suite."""

    parameter = '35'
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        super()._pass_run('ST35-III')
