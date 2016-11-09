#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for GEN8 Initial Test program."""

from .data_feed import UnitTester, ProgramTestCase
from programs import gen8

_PROG_CLASS = gen8.Initial
_PROG_LIMIT = gen8.INI_LIMIT


class Gen8Initial(ProgramTestCase):

    """GEN8 Initial program test suite."""

    prog_class = _PROG_CLASS
    prog_limit = _PROG_LIMIT

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensor
        dev = self.test_program.logdev
        dev.arm_ser.flushInput()        # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect': (
                    (sen.lock, 10.0), (sen.part, 10.0), (sen.fanshort, 200.0),
                    ),
                'Program': ((sen.o5v, 5.10), (sen.o3v3, 3.30), ),
                'PowerUp': (
                    (sen.acin, 240.0), (sen.o5v, (5.05, 5.11, )),
                    (sen.o12vpri, 12.12), (sen.o12v, 0.12),
                    (sen.o12v2, (0.12, 0.12, 12.12, )),
                    (sen.o24v, (0.24, 23.23, )), (sen.pwrfail, 0.0),
                    (sen.pfc,
                        (432.0, 432.0,      # Initial reading
                         442.0, 442.0,      # After 1st cal
                         440.0, 440.0,      # 2nd reading
                         440.0, 440.0,      # Final reading
                        )),
                    (sen.o12v,
                        (12.34, 12.34,      # Initial reading
                         12.24, 12.24,      # After 1st cal
                         12.14, 12.14,      # 2nd reading
                         12.18, 12.18,      # Final reading
                        )),
                    ),
                '5V': ((sen.o5v, (5.15, 5.14, 5.10)), ),
                '12V': (
                    (sen.o12v, (12.34, 12.25, 12.00)), (sen.vdsfet, 0.05),
                    ),
                '24V': (
                    (sen.o24v, (24.33, 24.22, 24.11)), (sen.vdsfet, 0.05),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise': ('', ) * 2,
                'PowerUp': ('', ) * 9 +
                    ('50Hz ', ) +       # ARM_AcFreq
                    ('240Vrms ', ) +    # ARM_AcVolt
                    ('5050mV ', ) +     # ARM_5V
                    ('12180mV ', ) +    # ARM_12V
                    ('24000mV ', ) +    # ARM_24V
                    (gen8.initial.limit.BIN_VERSION[:3], ) +    # ARM SwVer
                    (gen8.initial.limit.BIN_VERSION[4:], ),     # ARM BuildNo
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev.arm_puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(41, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PartDetect', 'Program', 'Initialise',
             'PowerUp', '5V', '12V', '24V'],
            self.tester.ut_steps)
