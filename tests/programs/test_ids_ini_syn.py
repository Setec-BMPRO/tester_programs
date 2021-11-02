#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 SynBuck Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500InitialSyn(ProgramTestCase):

    """IDS500 SynBuck Initial program test suite."""

    prog_class = ids500.InitialSyn
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['20VT'], 20.0), (sen['Minus20V'], -20.0),
                    (sen['9V'], 11.0), (sen['TECoutput'], 0.0),
                    (sen['LDDoutput'], 0.0), (sen['IS_Vmon'], 0.0),
                    (sen['IS_Iout'], 0.0), (sen['TEC_Vmon'], 0.0),
                    (sen['TEC_Vset'], 0.0),
                    ),
                'Program': (
                    (sen['Lock'], 10.0),
                    (sen['PicKit'], 0),
                    ),
                'TecEnable': (
                    (sen['TEC_Vmon'], (0.5, 2.5, 5.0)),
                    (sen['TECoutput'], (0.5, 7.5, 15.0)),
                    ),
                'TecReverse': (
                    (sen['TEC_Vmon'], (5.0,) * 2),
                    (sen['TECoutput'], (-15.0, 15.0)),
                    ),
                'LddEnable': (
                    (sen['LDDoutput'], (0.0, 0.65, 1.3)),
                    (sen['LDDshunt'], (0.0, 0.006, 0.05)),
                    (sen['IS_Iout'], (0.0, 0.6, 5.0)),
                    ),
                'ISSetAdj': (
                    (sen['IS_Iset'], (5.01, 5.01)), (sen['oAdjLdd'], True),
                    (sen['LDDshunt'], (0.0495, 0.0495, 0.05005)),
                    (sen['IS_Iout'], 5.0),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(34, len(result.readings))
        self.assertEqual(
            ['Program', 'PowerUp', 'TecEnable', 'TecReverse',
             'LddEnable', 'ISSetAdj'],
            self.tester.ut_steps)
