#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Console driver."""

import share


class InvalidOutputError(Exception):

    """Attempt to set a non-existing output."""


class _Console(share.console.Base):

    """Communications to RVMN101x and RVMN5x console.

    This class contains the present command syntax.
    See RVMN101B for the older version syntax.

    """

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b'\r\x1b[1;32muart:~$ \x1b[m'
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
    banner_lines = None         # Startup banner lines (set from config)
    max_output_index = 56       # Output index is range(max_output_index)
    missing_output_dict = {}    # Key: any text, Value: Output index
    reversed_output_dict = {}   # Key: any text, Value: Output index
    ls_0a5_out1 = 34
    ls_0a5_out2 = 35
    output_pin_name = {         # Key: Output index, Value: Schematic pin name
        0: 'HBRIDGE_1_extend',
        1: 'HBRIDGE_1_retract',
        2: 'HBRIDGE_2_extend',
        3: 'HBRIDGE_2_retract',
        4: 'HBRIDGE_3_extend',
        5: 'HBRIDGE_3_retract',
        6: 'HBRIDGE_4_extend',
        7: 'HBRIDGE_4_retract',
        8: 'HBRIDGE_5_extend',
        9: 'HBRIDGE_5_retract',
        10: 'HBRIDGE_6_extend',
        11: 'HBRIDGE_6_retract',
        12: 'HBRIDGE_7_extend',
        13: 'HBRIDGE_7_retract',
        14: 'HBRIDGE_8_extend',
        15: 'HBRIDGE_8_retract',
        16: 'HS_0A5_EN1',
        17: 'HS_0A5_EN2',
        18: 'HS_0A5_EN3',
        19: 'HS_0A5_EN4',
        20: 'HS_0A5_EN5',
        21: 'HS_0A5_EN6',
        22: 'HS_0A5_EN7',
        23: 'HS_0A5_EN8',
        24: 'HS_0A5_EN9',
        25: 'HS_0A5_EN10',
        26: 'HS_0A5_EN11',
        27: 'HS_0A5_EN12',
        28: 'HS_0A5_EN13',
        29: 'HS_0A5_EN14',
        30: 'HS_0A5_EN15',
        31: 'HS_0A5_EN16',
        32: 'HS_0A5_EN17',
        33: 'HS_0A5_EN18',
        34: 'LS_0A5_EN1',
        35: 'LS_0A5_EN2',
        36: 'Unused',
        37: 'Unused',
        38: 'OUT5A_EN0',
        39: 'OUT5A_EN1',
        40: 'OUT5A_EN2',
        41: 'OUT5A_EN3',
        42: 'OUT5A_EN4',
        43: 'OUT5A_EN5',
        44: 'OUT5A_PWM_EN6',
        45: 'OUT5A_PWM_EN7',
        46: 'OUT5A_PWM_EN8',
        47: 'OUT5A_PWM_EN9',
        48: 'OUT5A_PWM_EN10',
        49: 'OUT5A_PWM_EN11',
        50: 'OUT5A_PWM_EN12',
        51: 'OUT5A_PWM_EN13',
        52: 'OUT10A_1',
        53: 'OUT10A_2',
        54: 'OUT10A_3',
        55: 'OUT10A_4',
        }

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        missing_set = set()
        for key in self.missing_output_dict:
            missing_set.add(self.missing_output_dict[key])
        reversed_set = set()
        for key in self.reversed_output_dict:
            reversed_set.add(self.reversed_output_dict[key])
        self.normal_outputs = []        # List of normal output index
        self.reversed_outputs = []      # List of reversed output index
        for idx in range(self.max_output_index):
            if not (idx in missing_set or idx in reversed_set):
                self.normal_outputs.append(idx)
            if idx in reversed_set:
                self.reversed_outputs.append(idx)

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
        if not(index in self.normal_outputs or index in self.reversed_outputs):
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

    def pin_name(self, index):
        """Get the schematic name of an output pin.

        @param index Index number of the output

        """
        return self.output_pin_name[index]


class Console101A(_Console):

    """Communications to RVMN101A console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self.missing_output_dict = {
            'LS_0A5_EN1': 34,
            'LS_0A5_EN2': 35,
            'LS_0A5_EN3': 36,
            'LS_0A5_EN4': 37,
            }
        super().__init__(port)


class Console101B(_Console):

    """Communications to RVMN101B console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self.missing_output_dict = {
            'HBRIDGE 3 EXTEND': 4,
            'HBRIDGE 3 RETRACT': 5,
            'HBRIDGE 4 EXTEND': 6,
            'HBRIDGE 4 RETRACT': 7,
            'HBRIDGE 5 EXTEND': 8,
            'HBRIDGE 5 RETRACT': 9,
            'HS_0A5_EN5': 20,
            'HS_0A5_EN13': 28,
            'HS_0A5_EN14': 29,      # Implemented in Rev 14
            'HS_0A5_EN15': 30,      # Implemented in Rev 14
            'HS_0A5_EN18': 33,
            'LS_0A5_EN1': 34,
            'LS_0A5_EN2': 35,
            'LS_0A5_EN3': 36,
            'LS_0A5_EN4': 37,
            'OUT5A_PWM_13': 51,
            }
        super().__init__(port)

    def pin_name(self, index):
        """Get the schematic name of an output pin.

        @param index Index number of the output

        """
        # RVMN101B uses different names...
        return self.output_pin_name[index].replace('OUT10A_', 'OUT10AMP_')


class Console50(_Console):

    """Communications to RVMN5x console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self.missing_output_dict = {
            'HBRIDGE 2 EXTEND': 2,
            'HBRIDGE 2 RETRACT': 3,
            'HBRIDGE 3 EXTEND': 4,
            'HBRIDGE 3 RETRACT': 5,
            'HBRIDGE 7 EXTEND': 12,
            'HBRIDGE 7 RETRACT': 13,
            'HBRIDGE 8 EXTEND': 14,
            'HBRIDGE 8 RETRACT': 15,
            'HS_0A5_EN7': 22,
            'HS_0A5_EN13': 28,
            'HS_0A5_EN14': 29,
            'HS_0A5_EN15': 30,
            'HS_0A5_EN16': 31,
            'HS_0A5_EN17': 32,
            'HS_0A5_EN18': 33,
            'LS_0A5_EN1': 34,
            'LS_0A5_EN2': 35,
            'LS_0A5_EN3': 36,
            'LS_0A5_EN4': 37,
            'OUT5A_EN0': 38,
            'OUT5A_EN1': 39,
            'OUT5A_EN2': 40,
            'OUT5A_EN3': 41,
            'OUT5A_EN4': 42,
            'OUT5A_EN5': 43,
            'OUT5A_PWM_EN6': 44,
            'OUT5A_PWM_EN7': 45,
            'OUT5A_PWM_EN8': 46,
            'OUT10A_2': 53,
            'OUT10A_3': 54,
            'OUT10A_4': 55,
            }
        super().__init__(port)


class Console55(_Console):

    """Communications to RVMN55 console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        self.missing_output_dict = {
            'HBRIDGE 3 EXTEND': 4,
            'HBRIDGE 3 RETRACT': 5,
            'HBRIDGE 8 EXTEND': 14,
            'HBRIDGE 8 RETRACT': 15,
            'HS_0A5_EN7': 22,
            'HS_0A5_EN13': 28,
            'HS_0A5_EN14': 29,
            'HS_0A5_EN15': 30,
            'HS_0A5_EN16': 31,
            'HS_0A5_EN17': 32,
            'HS_0A5_EN18': 33,
            'LS_0A5_EN1': 34,
            'LS_0A5_EN2': 35,
            'LS_0A5_EN3': 36,
            'LS_0A5_EN4': 37,
            'OUT5A_EN0': 38,
            'OUT5A_EN1': 39,
            'OUT5A_EN2': 40,
            'OUT5A_EN3': 41,
            'OUT5A_EN4': 42,
            'OUT5A_EN5': 43,
            'OUT5A_PWM_EN6': 44,
            'OUT5A_PWM_EN7': 45,
            'OUT5A_PWM_EN8': 46,
            'OUT10A_2': 53,
            'OUT10A_3': 54,
            'OUT10A_4': 55,
            }
        super().__init__(port)
