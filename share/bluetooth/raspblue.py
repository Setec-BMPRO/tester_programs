#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONRPC Client for the Raspberry Pi Bluetooth helper."""

import jsonrpclib       # Install with: pip install jsonrpclib-pelix


class RaspberryBluetooth():

    """Connection to a Raspberry Pi with Bluetooth helper running."""

    # Default server URL (Static addressed)
    default_server = 'http://192.168.168.62:8888/'

    def __init__(self, server=None):
        """Create instance.

        @param server URL of the networked programmer

        """
        if server is None:
            server = self.default_server
        self.server = jsonrpclib.ServerProxy(
            server,
            config=jsonrpclib.config.Config(content_type='application/json')
            )
        self.response = bytearray()         # write() & read() buffer
        self.flushInput = lambda: None      # Dummy Serial method

    def write(self, bytes):
        """Simulate Serial.write

        @param bytes Byte data with appended '\r'

        """
        self.action(bytes[:-1].decode())    # call with '\r' removed

    def read(self, count=1):
        """Simulate Serial.read

        @param count Number of bytes to read
        @return Bytes read

        """
        return self.response.pop(0) if len(self.response) > 0 else None

    def echo(self, value):
        """Echo function for diagnostic purposes.

        @param value Input value to be echoed back
        @return The input value

        """
        return self.server.echo(value)

    def scan_blemac(self, blemac, timeout=10):
        """Scan for a device MAC address.

        @param blemac MAC address to locate
        @param timeout Timeout in seconds
        @return True if device was found

        """
        return self.server.scan_blemac(blemac, timeout)

    def scan_sernum(self, sernum, timeout=10):
        """Scan for a device Serial Number.

        @param sernum Serial Number to locate
        @param timeout Timeout in seconds
        @return True if device was found

        """
        return self.server.scan_blemac(sernum, timeout)

    def open(self, device_id, timeout=10):
        """Open a connection to a device console.

        @param device_id Serial Number OR MAC address to connect to
        @param timeout Timeout in seconds

        """
        self.server.open(device_id, timeout)

    def action(self, command, prompts=1, timeout=60):
        """Command-Response to an open console.

        @param command Command string to be sent
        @param prompts Number of prompts expected in the response
        @param timeout Timeout in seconds
        @return Response to the command

        """
        reply = self.server.action(command, prompts, timeout)
        self.response.clear()
        self.response.extend(reply.encode())
        return reply

    def close(self):
        """Close an open console."""
        self.server.close()
