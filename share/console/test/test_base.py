#!/usr/bin/env python3
"""UnitTest for console."""

import unittest
from share.sim_serial import SimSerial
from . import logging_setup

console = None      # Console module
mycon = None        # ConsoleGen2 instance


class ConsoleTestCase(unittest.TestCase):

    """Console test suite."""

    @classmethod
    def setUpClass(cls):
        """Hack import to get complete code coverage measurement."""
        logging_setup()
        global console
        import share.console as console_module
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
