#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SX750 Initial Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import sx750

_PROG_CLASS = sx750.Initial
_PROG_LIMIT = sx750.INI_LIMIT


class SX750Initial(ProgramTestCase):

    """SX750 Initial program test suite."""

    prog_class = _PROG_CLASS
    prog_limit = _PROG_LIMIT
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensor
        dev = self.test_program.logdev
        dev.arm_ser.flushInput()        # Flush console input buffer
        dev.ard_ser.flushInput()        # Flush Arduino input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'FixtureLock':(
                    (sen.Lock, 10.1), (sen.Part, 10.2), (sen.R601, 2001.0),
                    (sen.R602, 2002.0), (sen.R609, 2003.0), (sen.R608, 2004.0),
                    ),
                'Program': (
                    (sen.o5Vsb, 5.75), (sen.o5Vsbunsw, (5.0,) * 2),
                    (sen.o3V3, 3.21), (sen.o8V5Ard, 8.5), (sen.PriCtl, 12.34),
                    ),
                'Initialise': ((sen.o5Vsb, 5.75), (sen.o5Vsbunsw, 5.01), ),
                'PowerUp': (
                    (sen.ACin, 240.0), (sen.PriCtl, 12.34), (sen.o5Vsb, 5.05),
                    (sen.o12V, (0.12, 12.34)), (sen.o24V, (0.24, 24.34)),
                    (sen.ACFAIL, 5.0), (sen.PGOOD, 0.123),
                    (sen.PFC,
                        (432.0, 432.0,     # Initial reading
                         433.0, 433.0,     # After 1st cal
                         433.0, 433.0,     # 2nd reading
                         435.0, 435.0,     # Final value
                        )),
                    ),
                '5Vsb': ((sen.o5Vsb, (5.20, 5.15, 5.14, 5.10, )), ),
                '12V': (
                    (sen.o12V, (12.34, 12.25, 12.10, 12.00, 12.34, )),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 37 reads before OCP detected
                    (sen.o12VinOCP,
                        ((0.123, ) * 32 + (4.444, )) +
                        ((0.123, ) * 37 + (4.444, ))),
                    ),
                '24V': (
                    (sen.o24V, (24.44, 24.33, 24.22, 24.11, 24.24)),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 18 reads before OCP detected
                    (sen.o24VinOCP,
                        ((0.123, ) * 32 + (4.444, )) +
                        ((0.123, ) * 18 + (4.444, ))),
                    ),
                'PeakPower': (
                    (sen.o5Vsb, 5.15), (sen.o12V, 12.22), (sen.o24V, 24.44),
                    (sen.PGOOD, 0.15),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise': ('', ) * 2,   # arm
                'PowerUp': ('', ) +
                    ('50Hz ', ) +       # ARM_AcFreq
                    ('240Vrms ', ) +    # ARM_AcVolt
                    ('12180mV ', ) +    # ARM_12V
                    ('24000mV ', ) +    # ARM_24V
                    (sx750.initial.limit.BIN_VERSION[:3], ) +   # ARM SwVer
                    (sx750.initial.limit.BIN_VERSION[4:], ) +   # ARM BuildNo
                    ('', ) * 4,
                },
            UnitTester.key_ext: {       # Tuples of extra strings
                'Program': ('OK', ) * 3,    # ard
                '12V': ('OK', ) * 35,    # ard
                '24V': ('OK', ) * 35,    # ard
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push, dev.arm_puts, dev.ard_puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(58, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['FixtureLock', 'Program', 'Initialise', 'PowerUp',
             '5Vsb', '12V', '24V', 'PeakPower'],
            self.tester.ut_steps)
