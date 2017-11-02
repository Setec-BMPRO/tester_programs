#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONRPC Client for the Raspberry Pi Bluetooth helper."""

import jsonrpclib       # Install with: pip install jsonrpclib-pelix


class RaspberryBluetooth():

    """Connection to a Raspberry Pi with Bluetooth helper running."""

    # Default server URL (Static addressed)
    default_server = 'http://192.168.168.72:8888/'

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

    def echo(self, message):
        """Call the echo() method of the server.

        @param message Message to be echoed by the server.
        @return The server response

        """
        return self.server.echo(message)
