#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Console driver."""

import re

import share


class Console(share.console.Base):

    """Communications to RVSWT101 console."""

    re_banner = re.compile('^ble addr ([0-9a-f]{12})$')
    banner_lines = None

    def get_mac(self):
        """Get the MAC address from the console

        @return 12 hex digit Bluetooth MAC address

        """
        result = ''
        try:
            mac = self.action(None, delay=1.5, expected=self.banner_lines)
            if self.banner_lines > 1:
                mac = mac[0]
            mac = mac.replace(':', '')
            match = self.re_banner.match(mac)
            if match:
                result = match.group(1)
        except share.console.Error:
            pass
        return result

class DirectConsole(Console, share.console.BadUart):

    """Console for a direct connection."""
