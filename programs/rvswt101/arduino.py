#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""RVSWT101 Arduino console driver."""

import share

class Arduino(share.console.Base):

    """Communications to RVSWT101 Arduino console."""
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
    for n in range(1, 7):
        commands = (('PRESS_BUTTON_{}'.format(n), 'ACTU{};1'.format(n)),
                    ('RELEASE_BUTTON_{}'.format(n), 'ACTU{};0'.format(n)))
        for cmds in commands:
            cmd_data[cmds[0]] = share.console.parameter.String(cmds[1], writeable=True, write_format='{1}')

    def init_command(self, command):
        """init the console command."""
        self[command] = None


