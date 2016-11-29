#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Final Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import ids500

_PROG_CLASS = ids500.Final
_PROG_LIMIT = ids500.FIN_LIMIT


class Ids500Final(ProgramTestCase):

    """IDS500 Final program test suite."""

    prog_class = _PROG_CLASS
    prog_limit = _PROG_LIMIT

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen.arm_loads:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensor
        dev = self.test_program.logdev
        dev.pic_ser.flushInput()        # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp':
                    ((sen.Tec, 0.0), (sen.TecVmon, 0.0), (sen.Ldd, 0.0),
                     (sen.IsVmon, 0.0), (sen.o15V, 0.0), (sen.o_15V, 0.0),
                     (sen.o15Vp, 0.0), (sen.o15VpSw, 0.0), (sen.o5V, 0.0)),
                'KeySw1':
                    ((sen.Tec, 0.0), (sen.TecVmon, 0.0), (sen.Ldd, 0.0),
                     (sen.IsVmon, 0.0), (sen.o15V, 15.0), (sen.o_15V, -15.0),
                     (sen.o15Vp, 15.0), (sen.o15VpSw, 0.0), (sen.o5V, 5.0)),
                'KeySw12':
                    ((sen.Tec, 0.0), (sen.TecVmon, 240.0), (sen.Ldd, 0.0),
                     (sen.IsVmon, 0.0), (sen.o15V, 15.0), (sen.o_15V, -15.0),
                     (sen.o15Vp, 15.0), (sen.o15VpSw, 15.0), (sen.o5V, 5.0)),
                'TEC':
                    ((sen.TecVset, 5.05), (sen.TecVmon, (0.0, 4.99)),
                     (sen.Tec, (0.0, 15.0, -15.0)), (sen.oYesNoPsu, True),
                     (sen.oYesNoTecGreen, True), (sen.oYesNoTecRed, True)),
                'LDD':
                    ((sen.IsVmon, (2.0,) * 3), (sen.IsSet, (0.6, 5.0)),
                     (sen.IsIout, (0.0, 0.601, 5.01)),
                     (sen.IsOut, (0.0, 0.00602, 0.0502)),
                     (sen.oYesNoLddGreen, True), (sen.oYesNoLddRed, True)),
                'OCP':
                    ((sen.o5V, (5.0, ) * 21 + (3.9,), ),
                     (sen.o15Vp, (15.0, ) * 21 + (11.9,), ),
                     (sen.o15VpSw, (15.0, ) * 21 + (11.9,), ),
                     (sen.Tec, (15.0,) * 21 + (11.9,), ),
                     (sen.o15Vp, (15.0,) * 3), ),
                'Comms':
                    ((sen.oSerEntry, ('A1504010034',)), ),
                'EmergStop':
                    ((sen.Tec, 0.0), (sen.TecVmon, 0.0), (sen.Ldd, 0.0),
                     (sen.IsVmon, 0.0), (sen.o15V, 0.0), (sen.o_15V, 0.0),
                     (sen.o15Vp, 0.0), (sen.o15VpSw, 0.0), (sen.o5V, 0.0)),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Comms':
                    ('\r\n', 'M,1,Incorrectformat!Type?.?forhelp\r\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n') +
                    ('\r\nSetting Change Done\r\n\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n',
                    '\r\nSetting Change Done\r\n\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n',
                    'Software Test Mode Entered\r\n',
                    '\r\nSetting Change Done\r\n\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n') +
                    ('\r\nSetting Change Done\r\n\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n') +
                    ('I, 2, 06A,Hardware Revision\r\n', ) +
                    ('M,6,SettingisProtected\r\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n',
                    'M,3,UnknownCommand!Type?.?forhelp\r\n') +
                    ('I, 3, A1504010034,Serial Number\r\n', ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev.ids_puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(74, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'KeySw1', 'KeySw12', 'TEC', 'LDD', 'OCP',
              'Comms', 'EmergStop'],
            self.tester.ut_steps)
