#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for share.console."""

import unittest
from unittest.mock import patch
import tester
import share
from . import logging_setup


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
        # We need a tester to get MeasurementFailedError
        cls.tester = tester.Tester('MockATE', {}, fifo=True)

    @classmethod
    def tearDownClass(cls):
        cls.mycon.close()
        cls.patcher.stop()
        cls.tester.stop()

    def test_1_open(self):
        self.mycon.puts('\7Banner1\rBanner2\r> ')
        self.mycon.open()
        response = self.mycon.action()
        self.assertEqual(response, ['\7Banner1','Banner2'])

    def test_2_action(self):
        self.mycon.puts(' -> 1234\r> ')
        response = self.mycon.action('D')
        self.assertEqual(response, '1234')

    def test_3_noprompt(self):
        self.mycon.puts(' -> \r')
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NP')

    def test_4_noresponse(self):
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
        # We need a tester to get MeasurementFailedError
        cls.tester = tester.Tester('MockATE', {}, fifo=True)

    @classmethod
    def tearDownClass(cls):
        cls.mycon.close()
        cls.patcher.stop()
        cls.tester.stop()

    def test_1_open(self):
        self.mycon.puts('\7Banner1\r\nBanner2\r\n> ')
        self.mycon.open()
        response = self.mycon.action()
        self.assertEqual(response, ['\7Banner1','Banner2'])

    def test_2_action(self):
        self.mycon.puts(' -> 1234\r\n> ')
        response = self.mycon.action('D')
        self.assertEqual(response, '1234')

    def test_3_noprompt(self):
        self.mycon.puts(' -> \r\n')
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NP')

    def test_4_noresponse(self):
        with self.assertRaises(tester.MeasurementFailedError):
            self.mycon.action('NR')
