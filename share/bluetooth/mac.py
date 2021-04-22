#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""Bluetooth SerialNumber to MAC Storage."""

import jsonrpclib


class SerialToMAC():

    """Save/Read the blutooth MAC address for a Serial Number."""

    # The RPC server location
    server_url = 'https://webapp.mel.setec.com.au/ate/rpc/'

    def __init__(self):
        """Create the instance."""
        self.server = jsonrpclib.ServerProxy(self.server_url)

    def blemac_get(self, serial):
        """Retrieve a Bluetooth MAC for a Serial Number.

        @param serial Unit serial number ('AYYWWLLNNNN')
        @return 12 hex digit Bluetooth MAC address
            (which will be tested with a Measurement)

        """
        try:
            mac = self.server.blemac_get(serial)
        except jsonrpclib.jsonrpc.ProtocolError as exc:
            mac = str(exc)
        return mac

    def blemac_set(self, serial, blemac):
        """Save a Bluetooth MAC for a Serial Number.

        @param serial Unit serial number ('AYYWWLLNNNN')
        @param blemac Bluetooth MAC address (12 hex digits)

        """
        self.server.blemac_set(serial, blemac)
