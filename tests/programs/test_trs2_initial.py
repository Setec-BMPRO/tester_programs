#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRS2 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trs2


class TRSInitial(ProgramTestCase):

    """TRS2 Initial program test suite."""

    prog_class = trs2.Initial
    parameter = None
    debug = True

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['trs2_ser'].flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['tstpin_cover'], 0.0), (sen['vin'], 12.0),
                    (sen['3v3'], 3.30), (sen['brake'], (0.0, 12.0)),
                    ),
                'TestArm': (
                    (sen['light'], (11.9, 0.0)), (sen['remote'], (11.9, 0.0)),
                    (sen['red'], (3.1, 0.5, 3.1)),
                    (sen['green'], (3.1, 0.0, 3.1)),
                    (sen['blue'], (1.6, 0.25, 3.1)),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'TestArm':   ('Banner1\r\nBanner2\r\nBanner3', ) +
                                ('', ) * 4 +
                                (trs2.initial.Initial.arm_version, ) +
                                ('0x00000000', ) +
                                ('', ) * 15,
                'Bluetooth': ('F8F005FE6621', ) +
                                ('', ) * 2,
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev['trs2'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(23, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'TestArm', 'Bluetooth'],
            self.tester.ut_steps)