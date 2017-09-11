#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC2 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc2


class BC2Initial(ProgramTestCase):

    """BC2 Initial program test suite."""

    prog_class = bc2.Initial
    parameter = None
    debug = True
    btmac = '001EC030BC15'

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['bc2_ser'].flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['vin'], 12.0), (sen['3v3'], 3.30),
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
            dev['bc2'].puts,
            dev['ble'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(5, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(['Prepare', 'Bluetooth'], self.tester.ut_steps)
