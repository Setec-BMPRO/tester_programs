#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Configuration."""

import jsonrpclib


SW_VER = '1.0'
SW_IMAGE = 'rvswt101_{{0}}_{0}.hex'.format(SW_VER)
#                      ^- This is the program parameter


class SerialToMAC():

    """Save/Read the blutooth MAC address for a Serial Number."""

    # jsonrpclib uses non-standard 'application/json-rpc' by default
    #   Set the standard content_type here
    content_type = 'application/json'
    # The ERP server location
    server_url = 'http://localhost:8888/'

    def __init__(self):
        """Create the instance."""
        self.erp = jsonrpclib.ServerProxy(
            self.server_url,
            config=jsonrpclib.config.Config(content_type=self.content_type)
            )

    def blemac_get(self, serial):
        """Retrieve a Bluetooth MAC for a Serial Number.

        @param serial Unit serial number ('AYYWWLLNNNN')
        @return 12 hex digit Bluetooth MAC address

        """
        return self.erp.blemac_get(serial)

    def blemac_set(self, serial, blemac):
        """Save a Bluetooth MAC for a Serial Number.

        @param serial Unit serial number ('AYYWWLLNNNN')
        @param blemac Bluetooth MAC address (12 hex digits)

        """
        self.erp.blemac_set(serial, blemac)
