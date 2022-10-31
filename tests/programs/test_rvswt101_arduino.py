#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Arduino Console Test program."""

import unittest

import tester

from programs import rvswt101


class RVSWT101_Arduino_Console(unittest.TestCase):

    """RVMN101 Console program test suite."""

    prompt = "\r> "

    def setUp(self):
        """Per-Test setup."""
        port = tester.devphysical.sim_serial.SimSerial()
        port.echo = True
        self.con = rvswt101.arduino.Arduino(port)

    def test_all_commands(self):
        """Console operation."""
        consoleCommands = {
            "DEBUG": "DEBUG_ON",
            "QUIET": "DEBUG_OFF",
            "RETRACT_ACTUATORS": "ACTU_NONE",
            "EJECT_DUT": "ACTU_EJECT",
            "4BUTTON_MODEL": "4BUTTON",
            "6BUTTON_MODEL": "6BUTTON",
        }
        for button in range(1, 7):
            consoleCommands["PRESS_BUTTON_{0}".format(button)] = "ACTU{0};1".format(
                button
            )
            consoleCommands["RELEASE_BUTTON_{0}".format(button)] = "ACTU{0};0".format(
                button
            )
        for command in consoleCommands:
            with self.subTest(command=command):
                self.con.port.puts(self.prompt, preflush=1)
                self.con[command] = None
                expected = "{0}\r".format(consoleCommands[command]).encode()
                recvd = self.con.port.get()
                self.assertEqual(expected, recvd)
