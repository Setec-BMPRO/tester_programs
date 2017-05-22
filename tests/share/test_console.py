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
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls.patcher.start()
        sim_ser = tester.SimSerial(simulation=True)
        cls.mycon = share.console.BaseConsole(sim_ser, verbose=False)
        cls.mycon.open()
        # We need a tester to get MeasurementFailedError
        cls.tester = tester.Tester('MockATE', {}, fifo=True)

    @classmethod
    def tearDownClass(cls):
        cls.mycon.close()
        cls.patcher.stop()
        cls.tester.stop()

    def test_response2(self):
        """Multiple responses."""
        self.mycon.puts('R1\rR2\r> ')
        response = self.mycon.action(expected=2)
        self.assertEqual(response, ['R1','R2'])

    def test_response1(self):
        """A single response."""
        self.mycon.puts(' -> 1234\r> ')
        response = self.mycon.action('D', expected=1)
        self.assertEqual(response, '1234')

    def test_response_missing(self):
        """Not enough responses."""
        self.mycon.puts('R1\r> ')
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action(expected=2)

    @unittest.skip('Feature not implemented yet')
    def test_response_extra(self):
        """Too many responses."""
        self.mycon.puts('R1\rR2\r> ')
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action(expected=1)

    def test_noprompt(self):
        self.mycon.puts(' -> \r')
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NP')

    def test_noresponse(self):
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NR')


class BadUartConsole(unittest.TestCase):

    """BadUartConsole test suite."""

    @classmethod
    def setUpClass(cls):
        logging_setup()
        # Patch time.sleep to remove delays
        cls.patcher = patch('time.sleep')
        cls._sleep = cls.patcher.start()
        sim_ser = tester.SimSerial(simulation=True)
        cls.mycon = share.console.BadUartConsole(sim_ser, verbose=False)
        cls.mycon.open()
        # We need a tester to get MeasurementFailedError
        cls.tester = tester.Tester('MockATE', {}, fifo=True)

    @classmethod
    def tearDownClass(cls):
        cls.mycon.close()
        cls.patcher.stop()
        cls.tester.stop()

    def test_action2(self):
        self.mycon.puts('R1\r\nR2\r\n> ')
        response = self.mycon.action(expected=2)
        self.assertEqual(response, ['R1','R2'])

    def test_action1(self):
        self.mycon.puts(' -> 1234\r\n> ')
        response = self.mycon.action('D', expected=1)
        self.assertEqual(response, '1234')

    def test_noprompt(self):
        self.mycon.puts(' -> \r\n')
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NP')

    def test_noresponse(self):
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NR')
