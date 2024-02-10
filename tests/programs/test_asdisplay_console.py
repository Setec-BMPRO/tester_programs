#!/usr/bin/env python3
"""UnitTest for AsDisplay console driver."""

import unittest
from unittest.mock import Mock

from programs import asdisplay


class SerialResponder:

    """Generate a stream of bytes() of length 1 from strings."""

    def __init__(self):
        """Create instance."""
        self.buffer = []

    def append(self, str):
        """Append a string to the response list."""
        self.buffer.append(str)

    def bytes_generator(self):
        """Return generator of the strings as bytes() of length 1."""
        for a_str in self.buffer:
            for a_chr in a_str:
                yield (a_chr.encode())


class ASDisplayConsole(unittest.TestCase):

    """ASDisplay console program test suite."""

    def test_console(self):
        command_key = "TANK_LEVEL"
        command = "read_tank_level"
        response = "0x01,0x02,0x03,0x04"
        prompt = "\r\n>"
        # The serial port read() return values
        resp = SerialResponder()
        resp.append(command + "\r")  # Command echo
        resp.append(response)
        resp.append(prompt)
        # A Mock serial port
        port = Mock(name="port")
        port.read.side_effect = resp.bytes_generator()
        # Run the tank level command on the console
        mycon = asdisplay.console.Console(port)
        mycon.configure(command_key)
        reply = mycon.action(command, expected=1)
        self.assertEqual(
            (
                1,
                2,
                3,
                4,
            ),
            reply,
        )
