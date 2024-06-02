#!/usr/bin/env python3
"""UnitTest for Bluetooth."""

import unittest
from unittest.mock import Mock, patch

import share


class RaspberryBluetooth(unittest.TestCase):
    """Raspberry Pi Bluetooth test suite."""

    def setUp(self):
        self.server = Mock(name="MyServer")
        patcher = patch("jsonrpclib.ServerProxy", return_value=self.server)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.pibt = share.bluetooth.RaspberryBluetooth("")

    def test_echo(self):
        """Echo method."""
        value = "test"
        self.server.echo.return_value = value
        reply = self.server.echo(value)
        self.server.echo.assert_called_with(value)
        self.assertEqual(value, reply)

    def test_action(self):
        """Action method."""
        command = "command"
        response = "response\r\n> "
        # Simulate RPC server echo of the command
        self.server.action.return_value = command + "\r\n" + response
        reply = self.pibt.action(command)
        self.server.action.assert_called_with(command, 1, 60)
        self.assertEqual(response, reply)

    def test_action_cal(self):
        """Action method with CAL command."""
        command = "command CAL"
        response = "response\r\n> "
        # Simulate RPC server echo of the CAL command
        self.server.action.return_value = command + "\r\njunk line\r\n" + response
        reply = self.pibt.action(command)
        self.server.action.assert_called_with(command, 1, 60)
        self.assertEqual(response, reply)

    def test_write_read_cmd(self):
        """Write & read methods with whole commands."""
        command = b"command"
        response = "response\r\n> "
        # Simulate RPC server echo of the command
        self.server.action.return_value = command.decode() + "\r" + response
        self.pibt.write(command + b"\r")
        self.server.action.assert_called_with(command.decode(), 1, 60)
        read_data = self.pibt.read(len(command))
        self.assertEqual(command, read_data)
        read_data = self.pibt.read(100)
        self.assertEqual(b"\r" + response.encode(), read_data)

    def test_write_read(self):
        """Write & read methods byte-by-byte."""
        command = b"command"
        response = "response\r\n> "
        # Simulate RPC server echo of the command
        self.server.action.return_value = command.decode() + "\r" + response
        for abyte in command:
            self.pibt.write(bytes([abyte]))
        self.pibt.write(b"\r")
        self.server.action.assert_called_with(command.decode(), 1, 60)
        read_data = bytearray()
        reply = self.pibt.read()
        while len(reply) > 0:  # Read until no more data
            read_data.extend(reply)
            reply = self.pibt.read()
        self.assertEqual(bytearray(command + b"\r" + response.encode()), read_data)
