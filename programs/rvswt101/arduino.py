#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""RVSWT101 Final Test Program."""

import share

class Arduino(share.console.Base):

    """Communications to RVSWT101 Arduino console."""
    # Console command prompt. Signals the end of response data.
    cmd_data = {
        'DEBUG': share.console.parameter.String(
            'DEBUG_ON', writeable=True, write_format='{1}'),
        'QUIET': share.console.parameter.String(
            'DEBUG_OFF', writeable=True, write_format='{1}'),
        # Actuator commands
        'RETRACT_ACTUATORS': share.console.parameter.String(
            'ACTU_NONE', writeable=True, write_format='{1}'),
        'EJECT_DUT': share.console.parameter.String(
            'ACTU_EJECT', writeable=True, write_format='{1}'),
        # 4 or 6 button tester configuration
        '4BUTTON_MODEL': share.console.parameter.String(
            '4BUTTON', writeable=True, write_format='{1}'),
        '6BUTTON_MODEL': share.console.parameter.String(
            '6BUTTON', writeable=True, write_format='{1}'),
        }
    # Build all 6 PRESS_BUTTON and RELEASE_BUTTON actuator commands and add to cmd_data
    for n in range(6):
        commands = (('PRESS_BUTTON_{}'.format(n+1), 'ACTU{};1'.format(n+1)),
                    ('RELEASE_BUTTON_{}'.format(n+1), 'ACTU{};0'.format(n+1)))
        for cmds in commands:
            cmd_data[cmds[0]] = share.console.parameter.String(cmds[1], writeable=True, write_format='{1}')

    banner_lines = None         # Startup banner lines (set from config)
    max_output_index = 56       # Output index is range(max_output_index)
    missing_output_dict = {}    # Key: any text, Value: Output index
    reversed_output_dict = {}   # Key: any text, Value: Output index
    ls_0a5_out1 = 34
    ls_0a5_out2 = 35

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

    def check_command(self, command):
        self[command] = None





