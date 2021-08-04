#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""RVSWT101 Arduino console driver."""

import share

class Arduino(share.console.Base):

    """Communications to RVSWT101 Arduino console."""
    cmd_data = {
        'DEBUG': share.console.parameter.String('DEBUG_ON',
            writeable=True, write_format='{1}', read_format='{0}'),
        'QUIET': share.console.parameter.String('DEBUG_OFF',
            writeable=True, write_format='{1}', read_format='{0}'),
        # Actuator commands
        'RETRACT_ACTUATORS': share.console.parameter.String('ACTU_NONE',
            writeable=True, write_format='{1}', read_format='{0}'),
        'EJECT_DUT': share.console.parameter.String('ACTU_EJECT',
            writeable=True, write_format='{1}', read_format='{0}'),
        'EXERCISE': share.console.parameter.String('EXERCISE',
            writeable=True, write_format='{1}', read_format='{0}'),
        # 4 or 6 button tester configuration
        '4BUTTON_MODEL': share.console.parameter.String('4BUTTON',
            writeable=True, write_format='{1}', read_format='{0}'),
        '6BUTTON_MODEL': share.console.parameter.String('6BUTTON',
            writeable=True, write_format='{1}', read_format='{0}'),
        # UUT detection
        'UUT': share.console.parameter.String('UUT',
            writeable=True, write_format='{1}', read_format='{0}'),
        }

    # Build all 6 PRESS_BUTTON and RELEASE_BUTTON actuator commands and add to cmd_data
    for n in range(1, 7):
        commands = (('PRESS_BUTTON_{}'.format(n), 'ACTU{};1'.format(n)),
                    ('RELEASE_BUTTON_{}'.format(n), 'ACTU{};0'.format(n)))
        for test_cmd, arduino_cmd in commands:
            cmd_data[test_cmd] = share.console.parameter.String(arduino_cmd,
                writeable=True, write_format='{1}', read_format='{0}')

    def init_command(self, command):
        """init the console command."""
        self[command] = None



