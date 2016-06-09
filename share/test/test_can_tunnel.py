#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CAN Tunneled console."""

import unittest
import tester
from . import logging_setup

console = None      # Console module
mycon = None        # ConsoleCanTunnel instance


class TunnelTestCase(unittest.TestCase):

    """CAN Tunnel Console test suite."""

    @classmethod
    def setUpClass(cls):
        """Hack import to get complete code coverage measurement."""
        logging_setup()
        from .. import can_tunnel as console_module
        global console
        console = console_module
        sim_ser = tester.SimSerial(simulation=True)
        global mycon
        mycon = console.ConsoleCanTunnel(sim_ser)

    @classmethod
    def tearDownClass(cls):
        mycon.close()

    def test_1_open_fail(self):
        """No echo from the CAN interface."""
        with self.assertRaises(console.TunnelError):
            mycon.open()

    def test_2_open_ok(self):
        """Successful open."""
        mycon.port.puts('0 ECHO -> \r\n> ', preflush=1)
        mycon.port.puts('0x10000000\r\n', preflush=1)
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
