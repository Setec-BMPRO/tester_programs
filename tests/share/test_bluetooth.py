#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Bluetooth."""

import unittest
from unittest.mock import MagicMock, patch
import share


class Bluetooth(unittest.TestCase):

    """Bluetooth test suite."""

    mac_short = '001EC030BC15'
    mac_long = '00:1E:C0:30:BC:15'

    def test_short(self):
        """Create from short mac."""
        mac = share.bluetooth.MAC(self.mac_short)
        self.assertEqual(self.mac_short, mac.dumps())

    def test_long(self):
        """Create from long mac."""
        mac = share.bluetooth.MAC(self.mac_long)
        self.assertEqual(self.mac_short, mac.dumps())

    def test_bad(self):
        """Invalid mac."""
        with self.assertRaises(share.bluetooth.BluetoothError):
            share.bluetooth.MAC('junk')

    def test_str(self):
        """str(MAC)."""
        mac = share.bluetooth.MAC(self.mac_short)
        self.assertEqual(self.mac_short, str(mac))

    def test_dumps(self):
        """Dumping MAC as a string."""
        mac = share.bluetooth.MAC(self.mac_short)
        self.assertEqual(self.mac_short, mac.dumps())
        self.assertEqual(self.mac_long, mac.dumps(separator=':'))
        self.assertEqual(
            self.mac_long.replace(':', ' '), mac.dumps(separator=' '))
        self.assertEqual(
            self.mac_short.lower(), mac.dumps(lowercase=True))


class RaspberryBluetooth(unittest.TestCase):

    """Raspberry Pi Bluetooth test suite."""

    def setUp(self):
        self.server = MagicMock(name='MyServer')
        patcher = patch('jsonrpclib.ServerProxy', return_value=self.server)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('jsonrpclib.config.Config')
        self.addCleanup(patcher.stop)
        patcher.start()
        self.pibt = share.bluetooth.RaspberryBluetooth()

    def test_echo(self):
        """Echo method."""
        value = 'test'
        self.server.echo.return_value = value
        reply = self.server.echo(value)
        self.server.echo.assert_called_with(value)
        self.assertEqual(value, reply)

    def test_action(self):
        """Action method."""
        command = 'command'
        response = 'response'
        self.server.action.return_value = response
        reply = self.server.action(command)
        self.server.action.assert_called_with(command)
        self.assertEqual(response, reply)

    def test_write_read(self):
        """Write & read methods."""
        command = b'command\r'
        response = 'response\r\n> '
        self.server.action.return_value = response
        self.pibt.write(command)
        self.server.action.assert_called_with(
            command[:-1].decode(), 1, 60)
        read_data = bytearray()
        reply = self.pibt.read()
        while len(reply) > 0:       # Read until no more data
            read_data.extend(reply)
            reply = self.pibt.read()
        self.assertEqual(bytearray(response.encode()), read_data)
