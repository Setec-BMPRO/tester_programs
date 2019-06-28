#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101 Console driver."""

import share


class InvalidOutputError(Exception):

    """Attempt to set a non-existing output."""


class _Console(share.console.Base):

    """Communications to RVMN101A/B console."""

    max_output_index = 56       # Output index is range(max_output_index)
    missing_outputs = {}        # Key: any text, Value: Output index
    valid_outputs = []          # List of implemented output index
    ls_0a5_out1 = 34
    ls_0a5_out2 = 35

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        missing_set = set()
        for key in self.missing_outputs:
            missing_set.add(self.missing_outputs[key])
        for idx in range(self.max_output_index):
            if idx not in missing_set:
                self.valid_outputs.append(idx)

    def brand(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '03A'
        @param hardware_rev Hardware revision from Prod. Notes.

        """
        self.action(None, expected=self.banner_lines)
        self['SERIAL'] = sernum
        self['PRODUCT-REV'] = product_rev
        if hardware_rev:
            self['HARDWARE-REV'] = hardware_rev

    def hs_output(self, index, state=False):
        """Set a HS output state.

        @param index Index number of the output
        @param state True for ON, False for OFF

        """
        if index not in self.valid_outputs:
            raise InvalidOutputError
        self['OUTPUT'] = '{0} {1}'.format(index, 1 if state else 0)

    def ls_output(self, index, state=False):
        """Set a LS output state.

        @param index Index number of the output
        @param state True for ON, False for OFF

        """
        if index not in (self.ls_0a5_out1, self.ls_0a5_out2):
            raise InvalidOutputError
        self['OUTPUT'] = '{0} {1}'.format(index, 1 if state else 0)


class ConsoleA(_Console):

    """Communications to RVMN101A console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b'\r\x1b[1;32muart:~$ \x1b[m'
    # Number of startup banner lines, eg:
    #    ***** Booting Zephyr OS zephyr-v1.13.0-64-g7719dcb327 *****
    #    ***** Booting Zephyr OS zephyr-v1.14.0-119-g3632437c99b9 *****
    #    Reset reason:SREQ
    #    ***** RVGenius 1.1.0-0-g34c2c3a *****
    #
    #    uart:~$
    banner_lines = 4
    # Console commands
    parameter = share.console.parameter
    cmd_data = {
        'MAC': parameter.String(
            'rvmn mac', read_format='{0}'),
        'SERIAL': parameter.String(
            'rvmn serial', writeable=True, write_format='{1} {0}'),
        'PRODUCT-REV': parameter.String(
            'rvmn product-rev', writeable=True, write_format='{1} {0}'),
        'SW-REV': parameter.String(
            'rvmn sw-rev', read_format='{0}'),
        'HARDWARE-REV': parameter.String(
            'rvmn hw-rev', writeable=True, write_format='{1} {0}'),
        'OUTPUT': parameter.String(
            'rvmn output',
            readable=False, writeable=True, write_format='{1} {0}'),
        }

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self.missing_outputs = {
            'LS_0A5_EN1': 34,
            'LS_0A5_EN2': 35,
            'LS_0A5_EN3': 36,
            'LS_0A5_EN4': 37,
            }
        super().__init__(port)


class ConsoleB(_Console):

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

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self.missing_outputs = {
            'HBRIDGE 3 EXTEND': 4,
            'HBRIDGE 3 RETRACT': 5,
            'HBRIDGE 4 EXTEND': 6,
            'HBRIDGE 4 RETRACT': 7,
            'HBRIDGE 5 EXTEND': 8,
            'HBRIDGE 5 RETRACT': 9,
            'HS_0A5_EN5': 20,
            'HS_0A5_EN13': 28,
            'HS_0A5_EN14': 29,
            'HS_0A5_EN15': 30,
            'HS_0A5_EN18': 33,
            'LS_0A5_EN1': 34,
            'LS_0A5_EN2': 35,
            'LS_0A5_EN3': 36,
            'LS_0A5_EN4': 37,
            'OUT5A_PWM_13': 51,
            }
        super().__init__(port)
