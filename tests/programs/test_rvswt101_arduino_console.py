#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVMN101 Console Test program."""

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

    unittest doesn't support parameterized testing do we need a test case for each command
    The parameterized..

    """

    prompt = '\r> '

    def setUp(self):
        """Per-Test setup."""
        port = tester.devphysical.sim_serial.SimSerial()
        port.echo = True
        self.con = rvswt101.arduino.Arduino(port)
        self.con.measurement_fail_on_error = False

    def _builder(self, cmd):
        for _ in range(2):                      # 2 response prompts
            self.con.port.puts(self.prompt, preflush=1)

            self.con.check_command(cmd)

            expected = '{0}\r'.format(consoleCommands[cmd]).encode()
            recvd = self.con.port.get()
            self.assertEqual(expected, recvd)

    def test_all_commands(self):
        # Use subTest so all commands will run in one test case, but tests will continue on a failure.
        for cmd in consoleCommands:
            with self.subTest(msg=cmd):
                #self.assertEqual(cmd, cmd)
                self._builder(cmd)


