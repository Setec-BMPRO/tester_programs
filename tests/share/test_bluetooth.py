#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Bluetooth."""

import unittest
import share


class Bluetooth(unittest.TestCase):

    """Bluetooth test suite."""

    mac_short = '001EC030BC15'
    mac_long = '00:1E:C0:30:BC:15'

    def test_short(self):
        """Create from short mac."""
        mac = share.bluetooth.MAC(self.mac_short)
        self.assertEqual(self.mac_short, mac.dumps())
        self.assertEqual(self.mac_long, mac.dumps(separator=':'))

    def test_long(self):
        """Create from long mac."""
        mac = share.bluetooth.MAC(self.mac_long)
        self.assertEqual(self.mac_short, mac.dumps())
        self.assertEqual(
            self.mac_long.replace(':', ' '), mac.dumps(separator=' '))

    def test_bad(self):
        """Invalid mac."""
        with self.assertRaises(share.bluetooth.BluetoothError):
            share.bluetooth.MAC('junk')
