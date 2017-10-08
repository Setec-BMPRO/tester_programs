#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc2


class BC2Final(ProgramTestCase):

    """BC2 Final program test suite."""

    prog_class = bc2.Final
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Bluetooth': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['vin'], 12.0),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Bluetooth':
                    (self.btmac, ) +
                    ('', ) * 2,
                },
            UnitTester.key_ext: {       # Tuples of extra strings
                'Bluetooth': (
                    (None, 'AOK', ) +
                    (None, 'MCHP BTLE v1', ) +
                    (None, 'AOK', ) +
                    (self.btmac + ',0,,53....,-53', ) +
                    (None, 'AOK', )
                    ),
                },
            }
        self.tester.ut_load(
            data,
            self.test_program.fifo_push,
            lambda msg, addprompt: None,    # Dummy console.puts()
            dev['ble'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(3, len(result.readings))
        self.assertEqual(['Bluetooth', 'Cal'], self.tester.ut_steps)
