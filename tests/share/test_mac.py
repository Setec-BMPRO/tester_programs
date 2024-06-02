#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd.
"""UnitTest for MAC module."""

import unittest

import share


class MACtest(unittest.TestCase):
    """MAC test suite."""

    mac_bytes = b"\x00\x1e\xc00\xbc\x15"
    mac_short = "001EC030BC15"
    mac_long1 = "00:1E:C0:30:BC:15"
    mac_long2 = "00-1E-C0-30-BC-15"

    def test_bytes(self):
        """Create from bytes."""
        mac = share.MAC(self.mac_bytes)
        self.assertEqual(self.mac_short, mac.dumps(separator=""))

    def test_short(self):
        """Create from short mac."""
        mac = share.MAC.loads(self.mac_short)
        self.assertEqual(self.mac_short, mac.dumps(separator=""))

    def test_long1(self):
        """Create from long mac."""
        mac = share.MAC.loads(self.mac_long1)
        self.assertEqual(self.mac_short, mac.dumps(separator=""))

    def test_long2(self):
        """Create from long mac."""
        mac = share.MAC.loads(self.mac_long2)
        self.assertEqual(self.mac_short, mac.dumps(separator=""))

    def test_bad(self):
        """Invalid mac."""
        with self.assertRaises(ValueError):
            share.MAC.loads("junk")
        with self.assertRaises(ValueError):
            share.MAC(self.mac_bytes[1:])

    def test_dumps(self):
        """Dumping MAC as a string."""
        mac = share.MAC(self.mac_bytes)
        self.assertEqual(self.mac_short, mac.dumps(separator=""))
        self.assertEqual(self.mac_long1, mac.dumps(separator=":"))
        self.assertEqual(self.mac_long2, mac.dumps(separator="-"))
        self.assertEqual(
            self.mac_short.lower(), mac.dumps(separator="", lowercase=True)
        )

    def test_oui(self):
        """OUI mac."""
        mac = share.MAC(self.mac_bytes)
        self.assertEqual(self.mac_bytes[:3], mac.oui)

    def test_nic(self):
        """NIC mac."""
        mac = share.MAC(self.mac_bytes)
        self.assertEqual(self.mac_bytes[3:], mac.nic)

    def test_universal(self):
        """Universal mac."""
        mac = share.MAC(self.mac_bytes)
        self.assertTrue(mac.universal)

    def test_unicast(self):
        """Unicast mac."""
        mac = share.MAC(self.mac_bytes)
        self.assertTrue(mac.unicast)
