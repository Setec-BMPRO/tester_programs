#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TS3020H Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ts3020h


class TS3020HInitial(ProgramTestCase):

    """TS3020H Initial program test suite."""

    prog_class = ts3020h.Initial
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FixtureLock': (
                    (sen['oLock'], 10.0), (sen['oFanConn'], 150.0),
                    (sen['oInrush'], 160.0),
                    ),
                'FuseCheck': (
                    (sen['oVout'], 13.8), (sen['oSecCtl'], 13.5),
                    (sen['oSecCtl2'], 13.8), (sen['oGreenLed'], (2.0, 0.0)),
                    (sen['oRedLed'], (0.0, 2.0)),
                    ),
                'FanCheck': (
                    (sen['oFan12V'], (13.8, 0.5)), (sen['oSecShdn'], 13.0)
                    ),
                'OutputOV_UV': (
                    (sen['oSecShdn'], ((13.0, ) * 14 + (12.4, )) * 2, ),
                    ),
                'PowerUp': (
                    (sen['oVac'], 100.0), (sen['oAcDetect'], 11.0),
                    (sen['oInrush'], 5.0), (sen['oVbus'], (400.0, 30.0)),
                    (sen['oVout'], 13.8), (sen['oSecCtl'], 13.8),
                    (sen['oSecCtl2'], 13.8),
                    ),
                'MainsCheck': (
                    (sen['oAcDetect'], 4.0), (sen['oAcDetect'], 11.0),
                    (sen['oVac'], 240.0), (sen['oAcDetect'], 11.0),
                    (sen['oVbias'], 12.0), (sen['oSecCtl'], 13.8),
                    (sen['oVout'], 13.8),
                    ),
                'AdjOutput': (
                    (sen['oAdjVout'], True),
                    (sen['oVout'], (13.77, 13.80)),
                    ),
                'Load': (
                    (sen['oVbus'], 400.0), (sen['oVbias'], 12.0),
                    (sen['oSecCtl'], 13.8), (sen['oSecCtl2'], 13.8),
                    (sen['oVout'], (13.8, 13.8, 13.7, 0.0)),
                    ),
                'InputOV': (
                    (sen['oPWMShdn'], (10.0, 0.5)),
                    (sen['oVacOVShdn'], (10.0, 10.0)),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(45, len(result.readings))
        self.assertEqual(
            ['FixtureLock', 'FuseCheck', 'FanCheck', 'OutputOV_UV', 'PowerUp',
             'MainsCheck', 'AdjOutput', 'Load', 'InputOV'],
            self.tester.ut_steps)
