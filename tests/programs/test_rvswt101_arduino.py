#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Arduino Console Test program."""

import unittest

import tester

from programs import rvswt101

# create a lookup dict of known rvswt101 arduino console commands
consoleCommands = {'DEBUG': 'DEBUG_ON',
                   'QUIET': 'DEBUG_OFF',
                   'RETRACT_ACTUATORS': 'ACTU_NONE',
                   'EJECT_DUT': 'ACTU_EJECT',
                   '4BUTTON_MODEL': '4BUTTON',
                   '6BUTTON_MODEL': '6BUTTON',}
for n in range(6):
    consoleCommands['PRESS_BUTTON_{0}'.format(n+1)] = 'ACTU{0};1'.format(n+1)
    consoleCommands['RELEASE_BUTTON_{0}'.format(n+1)] = 'ACTU{0};0'.format(n+1)


class RVSWT101_Arduino_Console(unittest.TestCase):
    """RVMN101 Console program test suite.
    """

    prompt = '\r> '

    def setUp(self):
        """Per-Test setup."""
        port = tester.devphysical.sim_serial.SimSerial()
        port.echo = True
        self.con = rvswt101.arduino.Arduino(port)

    def test_all_commands(self):
        # Use subTest so all commands will run in one test case, but tests will continue on a failure.
        for cmd in consoleCommands:
            with self.subTest(cmd=cmd):
                self.con.port.puts(self.prompt, preflush=1)
                self.con.init_command(cmd)
                expected = '{0}\r'.format(consoleCommands[cmd]).encode()
                recvd = self.con.port.get()
                self.assertEqual(expected, recvd)

