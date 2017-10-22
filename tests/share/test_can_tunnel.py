#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CAN Tunneled console."""

import unittest
from unittest.mock import MagicMock
import share


class Tunnel(unittest.TestCase):

    """CAN Tunnel Console test suite."""

    targetid = 32       # CAN target device ID

    def setUp(self):
        self.interface = MagicMock(name='serial2can')
        self.mycon = share.ConsoleCanTunnel(self.interface, self.targetid)

    def test_open(self):
        """Open."""
        self.mycon.open()
        self.interface.open_tunnel.assert_called_once_with(self.targetid)

    def test_close(self):
        """Close."""
        self.mycon.close()
        self.interface.close_tunnel.assert_called_once_with()

    def test_write(self):
        """Write data."""
        data = b'hello'
        self.mycon.write(data)
        self.interface.write_tunnel.assert_called_once_with(data)

    def test_read(self):
        """Read data."""
        data = b'hello'
        self.interface.ready_tunnel = 0
        self.interface.read_tunnel.return_value = data
        read_data = self.mycon.read(size=len(data))
        self.assertEqual(data, read_data)
