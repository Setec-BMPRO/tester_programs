#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SelfTest program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import selftest


class SelfTest(ProgramTestCase):

    """SelfTest program test suite."""

    prog_class = selftest.Main
    parameter = None
    debug = False

    def _dso_store(self, value):
        """Fill all DSO sensors with a value."""
        sensors = self.test_program.sensors
        subsen = sensors['subchan']
        for sen in subsen:
            sen.store(value)
            sensors['oShield1'].store(0)
            sensors['oShield2'].store(0)
            sensors['oShield3'].store(0)
            sensors['oShield4'].store(0)

    def _dcs_store(self, value):
        """Fill all DC Source sensors with a value."""
        dcssen = self.test_program.sensors['dcs']
        for sen in dcssen:
            sen.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'ACSource': (
                    (sen['oAcs'], (120, 240)),
                    ),
                'Checker': (
                    (sen['o12V'], 12.0), (sen['o5Va'], 5.0),
                    (sen['o5Vb'], 5.0), (sen['o5Vc'], 5.0),
                    (sen['o5Vd'], 5.0), (sen['o5Ve'], 5.0),
                    ),
                'DSO': (
                    (sen['oShield1'], 6.0), (sen['oShield2'], 6.0),
                    (sen['oShield3'], 6.0), (sen['oShield4'], 6.0),
                    ),
                'DCLoad': (
                    (sen['oShunt'], (5e-3, 10e-3, 20e-3, 40e-3) * 7),
                    ),
                'RelayDriver': (
                    (sen['oRla12V'], 12.0),
                    (sen['oRla'], (0.5, 12.0) * 22),
                    ),
                'Discharge': (
                    (sen['oDisch1'], (10.0, 0.0)),
                    (sen['oDisch2'], (10.0, 0.0)),
                    (sen['oDisch3'], (10.0, 0.0)),
                    ),
                },
            UnitTester.key_call: {      # Callables
                'DSO': (
                    self._dso_store, ((8.0, 6.0, 4.0, 2.0, ), )
                    ),
                'DCSource': (
                    self._dcs_store, (5.0, 10.0, 20.0, 35.0, )
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(151, len(result.readings))
        self.assertEqual(
            ['ACSource', 'Checker', 'DSO', 'DCSource',
             'DCLoad', 'RelayDriver', 'Discharge'],
            self.tester.ut_steps)
