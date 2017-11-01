#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base classes for Bluetooth."""



class BluetoothError(Exception):

    """Bluetooth error."""


class BluetoothMAC():

    """Bluetooth MAC patterns."""

    # Regular expression for a MAC address
    regex = '[0-9A-F]{12}'
    # Regular expression for a string with only a MAC address
    line_regex = '^{0}$'.format(regex)
