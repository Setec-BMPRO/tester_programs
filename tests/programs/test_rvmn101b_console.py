#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMN101B Console Test program."""

import unittest
from unittest.mock import MagicMock, patch
import tester
from programs import rvmn101b


class RVMN101B_Console(unittest.TestCase):

    """RVMN101B Console program test suite."""

    prompt = '\r\n> '

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
        port = tester.devphysical.sim_serial.SimSerial()
        port.echo = True
        self.con = rvmn101b.console.Console(port)

    def test_output(self):
        """Output."""
#        relay = MagicMock()
#        self.con.port.puts('X\r\n' * 3 + self.prompt, preflush=1)
#        for _ in range(3):
#            self.con.port.puts(self.prompt, preflush=1)
#        self.con.initialise(relay)
#        written = self.con.port.get()
#        self.assertEqual(b'0xDEADBEA7 UNLOCK\rNV-DEFAULT\rNV-WRITE\r', written)
#        self.assertTrue(relay.pulse.called)
