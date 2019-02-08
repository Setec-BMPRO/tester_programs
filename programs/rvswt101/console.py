#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVSWT101 Console driver."""

import re
import share

class Console(share.console.BadUart):

    """Communications to RVSWT101 console."""

    re_banner = re.compile('^ble addr ([0-9a-f]{12})$')
    banner_lines = 1

    def get_mac(self):
        """Get the MAC address from the console

        @retunr 12 hex digit Bluetooth MAC address

        """
        mac = self.action(None, delay=1.5, expected=self.banner_lines)
        mac = mac.replace(':', '')
        match = self.re_banner.match(mac)
        if not match:
            raise ValueError('Bluetooth MAC not found in startup banner')
        return match.group(1)
