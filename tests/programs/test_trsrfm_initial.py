#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for TRSRFM Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trsrfm


class TRSRFMInitial(ProgramTestCase):

    """TRSRFM Initial program test suite."""

    prog_class = trsrfm.Initial
    parameter = None
    debug = True

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['trsrfm_ser'].flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1526040123', )),
                    (sen['tstpin_cover'], 0.0), (sen['vin'], 12.0),
                    (sen['3v3'], 3.30),
                    ),
                'TestArm': (
                    (sen['light'], (11.9, 0.0)),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'TestArm':   ('Banner1\r\nBanner2\r\nBanner3', ) +
                                ('', ) * 4 +
                                (trsrfm.initial.Initial.arm_version, ),
                'Bluetooth': ('F8F005FE6621', ) +
                                ('', ) * 2,
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev['trsrfm'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(10, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'TestArm', 'Bluetooth'],
            self.tester.ut_steps)