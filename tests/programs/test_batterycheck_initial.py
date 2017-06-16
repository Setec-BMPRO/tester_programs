#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BatteryCheck Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import batterycheck


class BatteryCheckInitial(ProgramTestCase):

    """BatteryCheck Initial program test suite."""

    prog_class = batterycheck.Initial
    parameter = None
    debug = False
    serial = 'A1509020010'

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['arm'].port.flushInput()    # Flush console input buffer
        dev['bt'].port.flushInput()     # Flush Bluetooth input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PreProgram':(
                    (sen['oSnEntry'], (self.serial, )),
                    (sen['reg5V'], 5.10),
                    (sen['reg12V'], 12.00),
                    (sen['o3V3'], 3.30),
                    ),
                'ARM': (
                    (sen['relay'], 5.0),
                    (sen['shunt'], 62.5 / 1250),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'InitialiseARM': (
                    ('Banner1\r\nBanner2', ) +  # Banner lines
                    ('', ) * 3
                    ),
                'ARM': (
                    ('-62000mA', ) +
                    ('', ) * 2 +
                    (batterycheck.initial.ARM_VERSION, ) +
                    ('12120', ) +
                    ('', )
                    ),
                },
            UnitTester.key_ext: {       # Tuples of extra strings
                'BlueTooth': (
                    (None, None, 'OK', ) +
                    (None, 'OK', ) +
                    (None, 'OK', ) +
                    ('+RDDSRES=112233445566,BCheck {},2,3'.format(
                        self.serial), ) +
                    ('+RDDSCNF=0', )
                    ),
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push,
            dev['arm'].puts, dev['bt'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(11, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PreProgram', 'InitialiseARM', 'ARM', 'BlueTooth'],
            self.tester.ut_steps)
