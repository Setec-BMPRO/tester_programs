#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GENIUS-II Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import genius2


class _Genius2Initial(ProgramTestCase):

    """GENIUS-II Initial program test suite."""

    prog_class = genius2.Initial

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen['olock'], 0.0), (sen['ovbatctl'], 13.0),
                     (sen['ovdd'], 5.0), (sen['diode'], 0.25), ),
                'Aux': ((sen['ovout'], 13.65), (sen['ovaux'], 13.70), ),
                'PowerUp':
                    ((sen['oflyld'], 30.0), (sen['oacin'], 240.0),
                     (sen['ovbus'], 330.0), (sen['ovcc'], 16.0),
                     (sen['ovbat'], 13.0), (sen['ovout'], 13.0),
                     (sen['ovdd'], 5.0), (sen['ovctl'], 12.0), ),
                'VoutAdj':
                    ((sen['oAdjVout'], True), (sen['ovout'], (13.65, 13.65, )),
                     (sen['ovbatctl'], 13.0), (sen['ovbat'], 13.65),
                     (sen['ovdd'], 5.0), ),
                'ShutDown':
                    ((sen['ofan'], (0.0, 13.0)),
                     (sen['ovout'], (13.65, 0.0, 13.65)),
                     (sen['ovcc'], 0.0), ),
                'OCP':
                    ((sen['ovout'], (13.5, ) * 11 + (13.0, ), ),
                     (sen['ovbat'], (self.vbat_ocp, 13.6)), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(28, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Aux', 'PowerUp', 'VoutAdj', 'ShutDown', 'OCP'],
            self.tester.ut_steps)

    def _fail_run(self):
        """FAIL 1st reading."""
        # Patch threading.Event & threading.Timer to remove delays
        mymock = MagicMock()
        mymock.is_set.return_value = True   # threading.Event.is_set()
        patcher = patch('threading.Event', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('threading.Timer', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen['olock'], 1000), ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(1, len(result.readings))
        self.assertEqual(['Prepare'], self.tester.ut_steps)


class _Genius2_Initial(_Genius2Initial):

    """GENIUS-II Initial program test suite."""

    parameter = 'STD'
    debug = False
    vbat_ocp = 3.6      # Vbat when loaded to 18A

    def test_pass_run(self):
        super()._pass_run()

    def test_fail_run(self):
        super()._fail_run()


class _Genius2_H_Initial(_Genius2Initial):

    """GENIUS-II-H Initial program test suite."""

    parameter = 'H'
    debug = False
    vbat_ocp = 13.6     # Vbat when loaded to 18A

    def test_pass_run(self):
        super()._pass_run()

    def test_fail_run(self):
        super()._fail_run()