#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CAN Tunneled console."""

import unittest
from unittest.mock import patch
import tester
from . import logging_setup

console = None      # Console module
mycon = None        # ConsoleCanTunnel instance


class Tunnel(unittest.TestCase):

    """CAN Tunnel Console test suite."""

    @classmethod
    def setUpClass(cls):
        """Hack import to get complete code coverage measurement."""
        logging_setup()
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls.patcher.start()
        import share.can_tunnel as console_module
        global console
        console = console_module
        sim_ser = tester.SimSerial(simulation=True)
        global mycon
        mycon = console.ConsoleCanTunnel(sim_ser, verbose=True)

    @classmethod
    def tearDownClass(cls):
        mycon.close()
        cls.patcher.stop()

    def test_1_open_fail(self):
        """No echo from the CAN interface."""
        with self.assertRaises(console.TunnelError):
            mycon.open()

    def test_2_open_ok(self):
        """Successful open."""
        mycon.port.puts('0 ECHO -> \r\n', preflush=1)
        mycon.port.puts('\r\n')
        mycon.port.puts('0x10000000\r\n\r\n')
        mycon.port.puts('\r\nRRC,32,3,3,0,16,1\r\n')
        mycon.open()

    def test_3_writeread(self):
        """Write & Read data."""
        mycon.port.puts('"RRC,32,4,7,87,79,82,76,68,13,10\r\n') # 'WORLD\r\n'
        mycon.port.get()    # Empty the output capture buffer
        mycon.write(b'HELLO\r')
        written = mycon.port.get()
        self.assertEqual(written, b'"TCC,32,4,72,69,76,76,79,13 CAN\r')
        reply = mycon.read(100)
        self.assertEqual(reply, b'WORLD\r\n')

    def test_4_read(self):
        """Read data."""
        mycon.port.puts('"RRC,32,4,7,87,79,82,76,68,13,10\r\n') # 'WORLD\r\n'
        reply = mycon.read(100)
        self.assertEqual(reply, b'WORLD\r\n')
