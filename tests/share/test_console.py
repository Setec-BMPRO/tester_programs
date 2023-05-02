#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for share.console."""

import unittest
from unittest.mock import patch

import tester

import share
from .. import logging_setup


class BaseConsole(unittest.TestCase):

    """BaseConsole test suite."""

    @classmethod
    def setUpClass(cls):
        logging_setup()
        # We need a tester to get MeasurementFailedError
        cls.tester = tester.Tester("MockATE", {})
        cls.tester.start()

    @classmethod
    def tearDownClass(cls):
        cls.tester.stop()

    def setUp(self):
        logging_setup()
        patcher = patch("time.sleep")  # Remove time delays
        self.addCleanup(patcher.stop)
        patcher.start()
        port = tester.devphysical.sim_serial.SimSerial()
        self.mycon = share.console.Base(port)
        self.addCleanup(self.mycon.close)
        self.mycon.open()
        tester.measure.Signals._reset()

    def test_response2(self):
        """Multiple responses."""
        self.mycon.port.puts("R1\rR2\r> ")
        response = self.mycon.action(expected=2)
        self.assertEqual(response, ["R1", "R2"])

    def test_response1(self):
        """A single response."""
        self.mycon.port.puts("D", preflush=1)
        self.mycon.port.puts(" -> 1234\r> ")
        response = self.mycon.action("D", expected=1)
        self.assertEqual(response, "1234")

    def test_response_missing(self):
        """Not enough responses."""
        self.mycon.port.puts("R1\r> ")
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action(expected=2)

    def test_response_extra(self):
        """Too many responses."""
        self.mycon.port.puts("R1\rR2\r> ")
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action(expected=1)

    def test_noprompt(self):
        self.mycon.port.puts(" -> \r")  # "> " is missing
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action("NP")

    def test_noresponse(self):
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action("NR")


class BadUartConsole(unittest.TestCase):

    """BadUartConsole test suite."""

    @classmethod
    def setUpClass(cls):
        logging_setup()
        # We need a tester to get MeasurementFailedError
        cls.tester = tester.Tester("MockATE", {})
        cls.tester.start()

    @classmethod
    def tearDownClass(cls):
        cls.tester.stop()

    def setUp(self):
        logging_setup()
        patcher = patch("time.sleep")  # Remove time delays
        self.addCleanup(patcher.stop)
        patcher.start()
        port = tester.devphysical.sim_serial.SimSerial()
        self.mycon = share.console.BadUart(port)
        self.addCleanup(self.mycon.close)
        self.mycon.open()
        tester.measure.Signals._reset()

    def test_action2(self):
        self.mycon.port.puts("R1\r\nR2\r\n> ")
        response = self.mycon.action(expected=2)
        self.assertEqual(response, ["R1", "R2"])

    def test_action1(self):
        self.mycon.port.puts("D", preflush=1)
        self.mycon.port.puts(" -> 1234\r\n> ")
        response = self.mycon.action("D", expected=1)
        self.assertEqual(response, "1234")

    def test_noprompt(self):
        self.mycon.port.puts(" -> \r\n")  # "> " is missing
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action("NP")

    def test_noresponse(self):
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action("NR")
