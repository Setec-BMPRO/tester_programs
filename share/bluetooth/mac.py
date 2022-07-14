#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""Bluetooth SerialNumber to MAC Storage."""

import attr
import jsonrpclib


@attr.s
class SerialToMAC():

    """Save/Read the bluetooth MAC address for a Serial Number."""

    server_url = attr.ib(default='https://webapp.mel.setec.com.au/ate/rpc/')

# FIXME: We should be able to reuse the ServerProxy
# ATE3b uses Python 3.10 with OpenSSL 3 and gets an "unexpected EOF" SSL
# error about 30 sec after the first RPC call.
# Use a new ServerProxy for every RPC call as a work around.

    def _server(self):
        """Create a new connection.

        @return jsonrpclib.ServerProxy instance

        """
        return jsonrpclib.ServerProxy(self.server_url)

    def blemac_get(self, serial):
        """Retrieve a Bluetooth MAC for a Serial Number.

        @param serial Unit serial number ('AYYWWLLNNNN')
        @return 12 hex digit Bluetooth MAC address

        """
        try:
            svr = self._server()
            mac = svr.blemac_get(serial)
            svr('close')
            del svr
        except Exception as exc:    # pylint: disable=broad-except
            mac = str(exc)
        return mac

    def blemac_set(self, serial, blemac):
        """Save a Bluetooth MAC for a Serial Number.

        @param serial Unit serial number ('AYYWWLLNNNN')
        @param blemac Bluetooth MAC address (12 hex digits)

        """
        svr = self._server()
        svr.blemac_set(serial, blemac)
        svr('close')
        del svr
