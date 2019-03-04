#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMN101B Console Test program."""

import unittest
from unittest.mock import patch
import tester
from programs import rvmn101b


class RVMN101B_Console(unittest.TestCase):

    """RVMN101B Console program test suite."""

    prompt = '\rrvmn> '

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
        sernum, rev = 'A1926010001', '03A'
        for aline in banner.split(sep='\n'):    # The banner lines
            self.con.port.puts(aline)
        for _ in range(2):                      # 2 response prompts
            self.con.port.puts(self.prompt, preflush=1)
        self.con.brand(sernum, rev)
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
        channel, setting = 12, 1
        self.con.port.puts(self.prompt, preflush=1)
        self.con.hs_output(channel, setting)
        self.assertEqual(
            'output {0} {1}\r'.format(channel, setting).encode(),
            self.con.port.get())
