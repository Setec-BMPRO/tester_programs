#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500Final(ProgramTestCase):

    """IDS500 Final program test suite."""

    prog_class = ids500.Final
    parameter = None
    debug = True  # False

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen.arm_loads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['pic_ser'].flushInput()     # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp':
                    ((sen['tec'], 0.0), (sen['tecvmon'], 0.0),
                     (sen['ldd'], 0.0), (sen['isvmon'], 0.0),
                     (sen['o15v'], 0.0), (sen['o_15v'], 0.0),
                     (sen['o15vp'], 0.0), (sen['o15vpsw'], 0.0),
                     (sen['o5v'], 0.0)),
                'KeySw1':
                    ((sen['tec'], 0.0), (sen['tecvmon'], 0.0),
                     (sen['ldd'], 0.0), (sen['isvmon'], 0.0),
                     (sen['o15v'], 15.0), (sen['o_15v'], -15.0),
                     (sen['o15vp'], 15.0), (sen['o15vpsw'], 0.0),
                     (sen['o5v'], 5.0)),
                'KeySw12':
                    ((sen['tec'], 0.0), (sen['tecvmon'], 240.0),
                     (sen['ldd'], 0.0), (sen['isvmon'], 0.0),
                     (sen['o15v'], 15.0), (sen['o_15v'], -15.0),
                     (sen['o15vp'], 15.0), (sen['o15vpsw'], 15.0),
                     (sen['o5v'], 5.0)),
                'TEC':
                    ((sen['tecvset'], 5.05), (sen['tecvmon'], (0.0, 4.99)),
                     (sen['tec'], (0.0, 15.0, -15.0)),
                     (sen['oYesNoPsu'], True),
                     (sen['oYesNoTecGreen'], True),
                     (sen['oYesNoTecRed'], True)),
                'LDD':
                    ((sen['isvmon'], (2.0,) * 3), (sen['isset'], (0.6, 5.0)),
                     (sen['isiout'], (0.0, 0.601, 5.01)),
                     (sen['isout'], (0.0, 0.00602, 0.0502)),
                     (sen['oYesNoLddGreen'], True),
                     (sen['oYesNoLddRed'], True)),
                'Comms':
                    ((sen['oSerNumEntry'], ('A1504010034',)),
                    (sen['oHwRevEntry'], ('07a ',)), ),
                'EmergStop':
                    ((sen['tec'], 0.0), (sen['tecvmon'], 0.0),
                     (sen['ldd'], 0.0), (sen['isvmon'], 0.0),
                     (sen['o15v'], 0.0), (sen['o_15v'], 0.0),
                     (sen['o15vp'], 0.0), (sen['o15vpsw'], 0.0),
                     (sen['o5v'], 0.0)),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Comms':
                    ('', 'M,1,Incorrectformat!Type?.?forhelp',
                    'M,3,UnknownCommand!Type?.?forhelp') +
                    ('', 'Setting Change Done', '',
                    '', 'Setting Change Done', '',
                    'Software Test Mode Entered',
                    '', 'Setting Change Done', '') +
                    ('', 'Setting Change Done', '') +
                    ('I, 2, 07A,Hardware Revision', ) +
                    ('M,6,SettingisProtected', '', '') +
                    ('I, 3, A1504010034,Serial Number', ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['pic'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(70, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'KeySw1', 'KeySw12', 'TEC', 'LDD',
             'Comms', 'EmergStop'],
            self.tester.ut_steps)
