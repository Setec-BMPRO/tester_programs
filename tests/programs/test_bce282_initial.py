#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BCE282-12/24 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bce282


class _BCE282Initial(ProgramTestCase):

    """BCE282 Initial program test suite."""

    prog_class = bce282.Initial

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['msp_ser'].flushInput()     # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['lock'], 10.0), (sen['vcc_bias'], 15.0),
                    ),
                'PowerUp': (
                    (sen['vac'], 240.0), (sen['vbus'], 340.0),
                    (sen['vcc_pri'], 15.5), (sen['vcc_bias'], 15.0),
                    (sen['vbat'], 0.0), (sen['alarm'], 2200),
                    ),
                'Calibration': (
                    (sen['vout'], (self.vout, ) * 2),
                    ),
                'OCP': (
                    (sen['alarm'], 12000),
                    (sen['vout'], (self.vout, ) * 15 + (self.inocp, ), ),
                    (sen['vbat'], (self.vout, ) * 15 + (self.inocp, ), ),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Calibration':
                    (' -> ', ) +
                    (' -> ', ) +
                    (' -> ', ) +
                    (' -> \r\x07BCE282 V3.0, build 2759.\r'
                        ' Built 11:57:54 on 8/8/2012.\r'
                        ' Error code: 1(p8=0, p16=0).\r'
                        ' Restart code: 4.', ) +
                    (' -> ', ) +
                    (' -> ', ) +
                    (' -> 0 ', ) +
                    (' -> ', ) +
                    (' -> ', ) +
                    # Both models respond with 12V output.
                    (' -> 13800 ', ) +
                    (' -> 1 ', ) +
                    (' -> ', ) +
                    (' -> 0 ', ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['msp'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(12, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'PowerUp', 'Calibration'],  # , 'OCP'],
            self.tester.ut_steps)


class BCE282_12_Initial(_BCE282Initial):

    """BCE282-12 Initial program test suite."""

    parameter = '12'
    vout = 13.8
    inocp = 12.9
    debug = True

    def test_pass_run(self):
        """PASS run of the 12 program."""
        super()._pass_run()


class BCE282_24_Initial(_BCE282Initial):

    """BCE282-12 Initial program test suite."""

    parameter = '24'
    vout = 27.7
    inocp = 25.9
    debug = False

    def test_pass_run(self):
        """PASS run of the 24 program."""
        super()._pass_run()
