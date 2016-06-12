#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for protocol."""

import unittest
import tester
from . import logging_setup

console = None      # Console module
mycon = None        # Console instance


class BaseConsoleTestCase(unittest.TestCase):

    """BaseConsole test suite."""

    @classmethod
    def setUpClass(cls):
        """Hack import to get complete code coverage measurement."""
        logging_setup()
        import share.console as console_module
        global console
        console = console_module
        sim_ser = tester.SimSerial(simulation=True)
        global mycon
        mycon = console.BaseConsole(sim_ser, verbose=True)

    @classmethod
    def tearDownClass(cls):
        mycon.close()

    def test_1_open(self):
        mycon.puts('\7Banner1\rBanner2\r> ')
        mycon.open()
        response = mycon.action()
        self.assertEqual(response, ['\7Banner1','Banner2'])

    def test_2_action(self):
        mycon.puts(' -> 1234\r> ')
        response = mycon.action('D')
        self.assertEqual(response, '1234')

    def test_3_noprompt(self):
        mycon.puts(' -> \r')
        with self.assertRaises(console.ConsoleResponseError):
            mycon.action('NP')

    def test_4_noresponse(self):
        with self.assertRaises(console.ConsoleResponseError):
            mycon.action('NR')


class BadUartConsoleTestCase(unittest.TestCase):

    """BadUartConsole test suite."""

    @classmethod
    def setUpClass(cls):
        """Hack import to get complete code coverage measurement."""
        logging_setup()
        import share.console as console_module
        global console
        console = console_module
        sim_ser = tester.SimSerial(simulation=True)
        global mycon
        mycon = console.BadUartConsole(sim_ser, verbose=True)

    @classmethod
    def tearDownClass(cls):
        mycon.close()

    def test_1_open(self):
        mycon.puts('\7Banner1\r\nBanner2\r\n> ')
        mycon.open()
        response = mycon.action()
        self.assertEqual(response, ['\7Banner1','Banner2'])

    def test_2_action(self):
        mycon.puts(' -> 1234\r\n> ')
        response = mycon.action('D')
        self.assertEqual(response, '1234')

    def test_3_noprompt(self):
        mycon.puts(' -> \r\n')
        with self.assertRaises(console.ConsoleResponseError):
            mycon.action('NP')

    def test_4_noresponse(self):
        with self.assertRaises(console.ConsoleResponseError):
            mycon.action('NR')
