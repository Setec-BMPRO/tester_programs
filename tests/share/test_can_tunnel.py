#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CAN Tunneled console."""

import unittest
from unittest.mock import patch
import tester
import share
from .. import logging_setup


class Tunnel(unittest.TestCase):

    """CAN Tunnel Console test suite."""

    def setUp(self):
        logging_setup()
        patcher = patch('time.sleep')   # Remove time delays
        self.addCleanup(patcher.stop)
        patcher.start()
        sim_ser = tester.SimSerial(simulation=True)
        self.mycon = share.can_tunnel.ConsoleCanTunnel(sim_ser, verbose=True)

    def test_1_open_fail(self):
        """No echo from the CAN interface."""
        with self.assertRaises(share.can_tunnel.TunnelError):
            self.mycon.open()

    def test_2_open_ok(self):
        """Successful open."""
        puts = self.mycon.port.puts
        puts('0 ECHO -> \r\n', preflush=1)
        puts('\r\n')
        puts('\r\n')
        puts('0x10000000\r\n\r\n')
        puts('\r\nRRC,32,3,3,0,16,1\r\n')
        self.mycon.open()

    def test_3_writeread(self):
        """Write & Read data."""
        self.mycon.port.puts(
            '"RRC,32,4,7,87,79,82,76,68,13,10\r\n') # 'WORLD\r\n'
        self.mycon.port.get()    # Empty the output capture buffer
        self.mycon.write(b'HELLO\r')
        written = self.mycon.port.get()
        self.assertEqual(written, b'"TCC,32,4,72,69,76,76,79,13 CAN\r')
        reply = self.mycon.read(100)
        self.assertEqual(reply, b'WORLD\r\n')

    def test_4_read(self):
        """Read data."""
        self.mycon.port.puts(
            '"RRC,32,4,7,87,79,82,76,68,13,10\r\n') # 'WORLD\r\n'
        reply = self.mycon.read(100)
        self.assertEqual(reply, b'WORLD\r\n')
