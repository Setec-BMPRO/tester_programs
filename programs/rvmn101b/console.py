#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101B Console driver."""

import share


class Console(share.console.Base):

    """Communications to RVMN101B console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b'\rrvmn> '
    # Number of startup banner lines, eg:
    #    ***** Booting Zephyr OS zephyr-v1.13.0-6-g04f6c719a *****
    #    Zephyr Shell, Zephyr version: 1.13.0
    #    Type 'help' for a list of available commands
    #    shell>
    #    rvmn>
    banner_lines = 4
    # Console commands
    parameter = share.console.parameter
    cmd_data = {
        'MAC': parameter.String(
            'mac', read_format='{0}'),
        'SERIAL': parameter.String(
            'serial', writeable=True, write_format='{1} {0}'),
        'PRODUCT-REV': parameter.String(
            'product-rev', writeable=True, write_format='{1} {0}'),
        'SW-REV': parameter.String(
            'sw-rev', read_format='{0}'),
        'OUTPUT': parameter.String(
            'output', readable=False, writeable=True, write_format='{1} {0}'),
        }

    def brand(self, sernum, product_rev):
        """Brand the unit with Serial Number."""
        self.action(None, expected=self.banner_lines)
        self['SERIAL'] = sernum
        self['PRODUCT-REV'] = product_rev

    def output(self, index, state=0):
        """Send an output command."""
        self['OUTPUT'] = '{0} {1}'.format(index, state)
