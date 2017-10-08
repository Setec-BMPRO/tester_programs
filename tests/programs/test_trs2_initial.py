#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS2 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class TRSInitial(ProgramTestCase):

    """TRS2 Initial program test suite."""

    prog_class = trs2.Initial
    parameter = None
    debug = False
    btmac = '001EC030BC15'

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['trs2'].port.flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['tstpin_cover'], 0.0),
                    (sen['vin'], 12.0),
                    (sen['3v3'], 3.30),
                    (sen['brake'], (0.0, 12.0)),
                    ),
                'Operation': (
                    (sen['light'], (11.9, 0.0)),
                    (sen['remote'], (11.9, 0.0)),
                    (sen['red'], (3.1, 0.5, 3.1)),
                    (sen['green'], (3.1, 0.0, 3.1)),
                    (sen['blue'], (1.6, 0.25, 3.1)),
                    ),
                'Calibrate': (
                    (sen['brake'], (0.3, 12.0)),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Operation':
                    ('', ) * 4 +
                    (trs2.initial.Initial.arm_version, ) +
                    ('0x00000000', ) +
                    ('', ) * 15,
                'Calibrate':
                    ('x', ) * 2 +
                    ('', '12001', '12002', '101', '102', ),
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
            dev['trs2'].puts,
            dev['ble'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(29, len(result.readings))
        self.assertEqual(
            ['Prepare', 'Operation', 'Calibrate', 'Bluetooth'],
            self.tester.ut_steps)
