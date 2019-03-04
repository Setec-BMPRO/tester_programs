#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101B Console driver."""

import share

class InvalidOutputError(Exception):

    """Attempt to set a missing output."""


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
    max_output_index = 56
    ls_0a5_out1 = 34
    ls_0a5_out2 = 35

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        missing_outputs = {
            'HBRIDGE3 EXTEND': 4,
            'HBRIDGE3 RETRACT': 5,
            'HBRIDGE4 EXTEND': 6,
            'HBRIDGE4 RETRACT': 7,
            'HBRIDGE5 EXTEND': 8,
            'HBRIDGE5 RETRACT': 9,
            'HS_0A5_OUT5': 20,
            'HS_0A5_OUT13': 28,
            'HS_0A5_OUT14': 29,
            'HS_0A5_OUT15': 30,
            'HS_0A5_OUT18': 33,
            'LS_0A5_OUT1': 34,
            'LS_0A5_OUT2': 35,
            'LS_0A5_OUT3': 36,
            'LS_0A5_OUT4': 37,
            'OUT5A_13': 51,
            }
        missing_set = set()
        for key in missing_outputs:
            missing_set.add(missing_outputs[key])
        self.valid_outputs = []
        for idx in range(self.max_output_index):
            if idx not in missing_set:
                self.valid_outputs.append(idx)

    def brand(self, sernum, product_rev):
        """Brand the unit with Serial Number."""
        self.action(None, expected=self.banner_lines)
        self['SERIAL'] = sernum
        self['PRODUCT-REV'] = product_rev

    def hs_output(self, index, state=0):
        """Send a HS output command."""
        if index not in self.valid_outputs:
            raise InvalidOutputError
        self['OUTPUT'] = '{0} {1}'.format(index, state)

    def ls_output(self, index, state=0):
        """Send a LS output command."""
        self['OUTPUT'] = '{0} {1}'.format(index, state)
