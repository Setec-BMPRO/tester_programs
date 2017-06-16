#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BatteryCheck Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import batterycheck


class BatteryCheckFinal(ProgramTestCase):

    """BatteryCheck Final program test suite."""

    prog_class = batterycheck.Final
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['bt'].port.flushInput()     # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['oSnEntry'], ('A1509020010', )),
                    (sen['o12V'], 12.0),
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'TestBlueTooth':
                    (None, None, 'OK\r\n', ) +
                    (None, 'OK\r\n', ) +
                    (None, 'OK\r\n', ) +
                    ('+RDDSRES=112233445566,BCheck A1509020010,2,3\r\n', ) +
                    ('+RDDSCNF=0\r\n', ) +
                    (None, 'OK\r\n', ) +
                    ('+RPCI=\r\n', )  +         # Ask for PIN
                    (None, 'OK\r\n', ) +
                    ('+RUCE=\r\n', ) +          # Ask for 6-digit verify
                    (None, 'OK\r\n', ) +
                    ('+RCCRCNF=500,0000,0\r\n', ) +     # Pair response
                    (None, 'OK\r\n', ) +
                    (None, '{"jsonrpc": "2.0","id": 8256,'
                     '"result": {"HardwareVersion": "2.0",'
                     '"SoftwareVersion": '
                     '"' + batterycheck.final.ARM_VERSION + '",'
                     '"SerialID": "A1509020010"}}\r\n', ) +
                    (None, 'OK\r\n', ) +
                    (None, 'OK\r\n', ) +
                    ('+RDII\r\n', )
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['bt'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(6, len(result.readings))   # Reading count
        # And did all steps run in turn?
        self.assertEqual(['PowerUp', 'TestBlueTooth'], self.tester.ut_steps)
