#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2014 SETEC Pty Ltd.
"""Base classes for Bluetooth."""
# TODO: Remove this deprecated file once eunistone_pan1322 is gone

import re


class BluetoothError(Exception):

    """Bluetooth error."""


class MAC():

    """Bluetooth MAC address."""

    # Regular expression for a MAC address, with optional ':' characters
    regex = '(?:[0-9A-F]{2}:?){5}[0-9A-F]{2}'
    # Regular expression for a string with only a MAC address
    line_regex = '^{0}$'.format(regex)

    def __init__(self, mac):
        """Create a MAC instance.

        @param mac MAC as a string

        """
        if not re.match(self.line_regex, mac):
            raise BluetoothError('Invalid MAC string')
        self._mac = bytes.fromhex(mac.replace(':', ''))

    def __str__(self):
        """MAC address as a string.

        @return MAC address as 12 uppercase hex digits

        """
        return self.dumps()

    def dumps(self, separator='', lowercase=False):
        """Dump the MAC as a string.

        @param separator String to separate the bytes.
        @param lowercase Convert to lowercase.
        @return MAC as a string.

        """
        data = []
        for abyte in self._mac:
            data.append('{0:02X}'.format(abyte))
        data_str = separator.join(data)
        if lowercase:
            data_str = data_str.lower()
        return data_str
