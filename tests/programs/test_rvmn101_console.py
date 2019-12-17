#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMN101 Console Test program."""

import unittest

import tester

from programs import rvmn101


class RVMN101B_Console(unittest.TestCase):

    """RVMN101 Console program test suite."""

    prompt = '\rrvmn> '

    def setUp(self):
        """Per-Test setup."""
        port = tester.devphysical.sim_serial.SimSerial()
        port.echo = True
        self.con = rvmn101.console.ConsoleB(port)
        self.con.banner_lines = 4
        # Allow exceptions from the console driver
        self.con.measurement_fail_on_error = False

    def test_brand(self):
        """Branding unit with serial number & revision."""
        banner = (
            '***** Booting Zephyr OS zephyr-v1.13.0-6-g04f6c719a *****\r\n'
            'Zephyr Shell, Zephyr version: 1.13.0\r\n'
            "Type 'help' for a list of available commands\r\n"
            'shell>\r\n'
            'rvmn> '
            )
        sernum, rev, hw_rev = 'A1926010001', '03A', None
        for aline in banner.split(sep='\n'):    # The banner lines
            self.con.port.puts(aline)
        for _ in range(2):                      # 2 response prompts
            self.con.port.puts(self.prompt, preflush=1)
        self.con.brand(sernum, rev, hw_rev)
        self.assertEqual(
            'serial {0}\rproduct-rev {1}\r'.format(sernum, rev).encode(),
            self.con.port.get())

    def test_mac(self):
        """Bluetooth MAC reading."""
        mac = '11:22:33:44:55:66 (random)'
        self.con.port.puts(mac + '\r\n' + self.prompt, preflush=1)
        self.assertEqual(mac, self.con['MAC'])
        self.assertEqual(b'mac\r', self.con.port.get())

    def test_hs_output(self):
        """Output driver command."""
        channel, setting = 12, True
        self.con.port.puts(self.prompt, preflush=1)
        self.con.hs_output(channel, setting)
        self.assertEqual(
            'output {0} {1}\r'.format(channel, 1 if setting else 0).encode(),
            self.con.port.get())
