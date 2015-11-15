#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for console."""

import unittest
from ...sim_serial import SimSerial
from . import logging_setup

console = None      # Console module
mycon = None        # ConsoleGen2 instance


class ConsoleTestCase(unittest.TestCase):

    """Console test suite."""

    @classmethod
    def setUpClass(cls):
        """Hack import to get complete code coverage measurement."""
        logging_setup()
        from ... import console as console_module
        global console
        console = console_module
        sim_ser = SimSerial(simulation=True)
        global mycon
        mycon = console.ConsoleGen2(sim_ser)

    @classmethod
    def tearDownClass(cls):
        mycon.close()

    def test_open(self):
        mycon.puts(
            'BC15\r\n'                          # BEGIN Startup messages
            'Build date:       06/11/2015\r\n'
            'Build time:       15:31:40\r\n'
            'SystemCoreClock:  48000000\r\n'
            'Software version: 1.0.11705.1203\r\n'
            'nonvol: reading crc invalid at sector 14 offset 0\r\n'
            'nonvol: reading nonvol2 OK at sector 15 offset 2304\r\n'
            'Hardware version: 0.0.[00]\r\n'
            'Serial number:    A9999999999\r\n'
            'Please type help command.\r\n'
            '> '                                # END Startup messages
            '"OK\\n PROMPT\r\n'                 # 1st command echo
            'OK\r\n'                            # and it's response
            '0 ECHO\r\nOK\r\n'                  # ECHO command echo
            'OK\r\n'                            # and it's response
            )
        mycon.open()

    def test_stat(self):
        mycon.puts(
            '# error blink count...\r\n'        # BEGIN Stat response
            '# battery: solid\r\n'
            '# polarity 1\r\n'
            '# temperature 2\r\n'
            '# short 3\r\n'
            '# over volt 4\r\n'
            '# under volt 5\r\n'
            'used-data=0x91C\r\n'
            'free-data=0x16E4\r\n'
            'used-stack=0xD8\r\n'
            'free-stack=0x160C\r\n'
            'pri-temp=679 ;degCx10\r\n'
            'sec-temp=252 ;degCx10\r\n'
            'pulsing-open-volts=13722 ;mV (=N/A if not pulsing)\r\n'
            'pulsing-open-current=18 ;mA (=N/A if not pulsing)\r\n'
            'pulsing-closed-volts=13722 ;mV (=N/A if not pulsing)\r\n'
            'pulsing-closed-current=18 ;mA (=N/A if not pulsing)\r\n'
            'not-pulsing-volts=N/A ;mV (=N/A because pulsing)\r\n'
            'not-pulsing-current=N/A ;mA (=N/A because pulsing)\r\n'
            'batt-detect=OVERVOLT ;mV'
                ' (NOINFO/NOBATT/SHORT/POLARITY/OVERVOLT)\r\n'
            'volts-open-closed-rawadc=877 877\r\n'
            'current-open-closed-rawadc=1 1\r\n'
            'battdetect-open-closed-volts-rawadc=2 2\r\n'
            'sec-temp-rawadc=929\r\n'
            'overvolt-latch=0 ;(r) resets\r\n'
            'fan-enable=0\r\n'
            'dcdc-enable=1 ;(e) toggles\r\n'
            'dcdcout-enable=1 ;(o) toggles\r\n'
            'ps-on=0 ;(p) toggles\r\n'
            'mv-set=13650 ;mV\r\n'
            'ma-set=15000 ;mA\r\n'
            'logm=0x0\r\n'
            'mainloop-run=1\r\n'
            'mainloop-ms=100\r\n'
            'mainloop-errors=0\r\n'
            'chemistry=AGM\r\n'
            'chargemode=CHARGEHIGHAMP\r\n'
            'chargestate=FLOAT\r\n'
            '# LEDs: .=off *=on @=blinking\r\n'
            '# Fault=red + Stage1=green (bi-color)\r\n'
            '# SizeC=green + SizeD =yellow (bi-color)\r\n'
            '# Fault__Stage1 2 3 4 5 6 ChemA B C D SizeA B C__D\r\n'
            '# . * * * * * * * . . . . . * .\r\n'       # END Stat response
            'OK\r\n'                            # and the final prompt
            )
        mycon.stat()
        # Must have read correct number of values
        self.assertEqual(len(mycon.stat_data), 31)
