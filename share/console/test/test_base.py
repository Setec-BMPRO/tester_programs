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

    def test_open(self):
        mycon.puts('Banner1\r\nBanner2\r\nVersion\r\n'  # Startup junk
                   'OK\\n PROMPT\r\n'                   # 1st command echo
                   'OK\r\n'                             # and it's response
                   'OK\r\n')                            # ECHO response
        mycon.open()
