#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CAN Tunneled console."""

import unittest
from unittest.mock import MagicMock
import tester
import share


class Tunnel(unittest.TestCase):

    """CAN Tunnel Console test suite."""

    targetid = share.can.ID.trek2       # CAN target device ID

    def setUp(self):
        self.interface = MagicMock(name='serial2can')
        self.mycon = share.can.Tunnel(self.interface, self.targetid)

    def test_open(self):
        """Open."""
        self.mycon.open()
        self.interface.open_tunnel.assert_called_once_with(self.targetid)

    def test_open_error(self):
        """Open error."""
        # We need a tester to get MeasurementFailedError
        mytester = tester.Tester('MockATE', {})
        self.interface.open_tunnel.side_effect = tester.SerialToCanError
        try:
            with self.assertRaises(tester.MeasurementFailedError):
                self.mycon.open()
        finally:
            mytester.stop()

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
