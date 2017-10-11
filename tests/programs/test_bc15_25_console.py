#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15/25 Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch
import tester
from programs import bc15_25


class BC25_Console(unittest.TestCase):

    """BC25 Console program test suite."""

    @classmethod
    def setUpClass(cls):
        # We need a tester to get MeasurementFailedError.
        cls.tester = tester.Tester('MockATE', {})

    @classmethod
    def tearDownClass(cls):
        cls.tester.stop()

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'time.sleep',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        port = tester.SimSerial()
        self.con = bc15_25.console.Console(port)

    def test_nobanner(self):
        """Missing banner lines."""
        with self.assertRaises(tester.MeasurementFailedError):
            self.con.action(None, expected=3)

    def test_banner(self):
        """Banner lines present."""
        self.con.port.puts('X\r\n' * 3 + '\r\n> ')
        self.con.banner()

    def test_initialise(self):
        """Initialise."""
        relay = MagicMock()
        self.con.port.puts('X\r\n' * 3 + '\r\n> ', preflush=1)
        for cmd in (
                '0xDEADBEA7 UNLOCK',
                'NV-DEFAULT',
                'NV-WRITE',
                ):
            self.con.port.puts(cmd + '\r\n> ', preflush=1)
        self.con.initialise(relay)
