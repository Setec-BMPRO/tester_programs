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

    def test_long(self):
        """Create from long mac."""
        mac = share.bluetooth.MAC(self.mac_long)
        self.assertEqual(self.mac_short, mac.dumps())

    def test_bad(self):
        """Invalid mac."""
        with self.assertRaises(share.bluetooth.BluetoothError):
            share.bluetooth.MAC('junk')

    def test_str(self):
        """str(MAC)."""
        mac = share.bluetooth.MAC(self.mac_short)
        self.assertEqual(self.mac_short, str(mac))

    def test_dumps(self):
        """Dumping MAC as a string."""
        mac = share.bluetooth.MAC(self.mac_short)
        self.assertEqual(self.mac_short, mac.dumps())
        self.assertEqual(self.mac_long, mac.dumps(separator=':'))
        self.assertEqual(
            self.mac_long.replace(':', ' '), mac.dumps(separator=' '))
        self.assertEqual(
            self.mac_short.lower(), mac.dumps(lowercase=True))
