#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""RVSWT101 Final Test Program."""

import share


class Arduino(share.console.Base):

    """Communications to RVSWT101 Arduino console."""

    cmd_data = {
        'DEBUG': share.console.parameter.String(
            'DEBUG_ON', read_format='{0}'),
        'QUIET': share.console.parameter.String(
            'DEBUG_OFF', read_format='{0}'),
        # Actuator commands
#        'PRESS_BUTTON_1': share.console.parameter.String(
#            'ACTU1;1', read_format='{0}'),
#        'PRESS_BUTTON_2': share.console.parameter.String(
#            'ACTU2;1', read_format='{0}'),
#        'PRESS_BUTTON_3': share.console.parameter.String(
#            'ACTU3;1', read_format='{0}'),
#        'PRESS_BUTTON_4': share.console.parameter.String(
#            'ACTU4;1', read_format='{0}'),
#        'PRESS_BUTTON_5': share.console.parameter.String(
#            'ACTU5;1', read_format='{0}'),
#        'PRESS_BUTTON_6': share.console.parameter.String(
#            'ACTU6;1', read_format='{0}'),
#        'RELEASE_BUTTON_1': share.console.parameter.String(
#            'ACTU1;0', read_format='{0}'),
#        'RELEASE_BUTTON_2': share.console.parameter.String(
#            'ACTU1;0', read_format='{0}'),
#        'RELEASE_BUTTON_3': share.console.parameter.String(
#            'ACTU1;0', read_format='{0}'),
#        'RELEASE_BUTTON_4': share.console.parameter.String(
#            'ACTU1;0', read_format='{0}'),
#        'RELEASE_BUTTON_5': share.console.parameter.String(
#            'ACTU1;0', read_format='{0}'),
#        'RELEASE_BUTTON_6': share.console.parameter.String(
#            'ACTU1;0', read_format='{0}'),
        'RETRACT_ACTUATORS': share.console.parameter.String(
            'ACTU_NONE', read_format='{0}'),
        'EJECT_DUT': share.console.parameter.String(
            'ACTU_EJECT', read_format='{0}'),
        # 4 or 6 button tester configuration
        '4BUTTON_MODEL': share.console.parameter.String(
            '4BUTTON', read_format='{0}'),
        '6BUTTON_MODEL': share.console.parameter.String(
            '6BUTTON', read_format='{0}'),
        }
        
    # Build all 6 PRESS_BUTTON and RELEASE_BUTTON commands and add to cmd_data
    for n in range(6):
        commands = (('PRESS_BUTTON_{}'.format(n+1), 'ACTU{};1'.format(n+1)),
                    ('RELEASE_BUTTON_{}'.format(n+1), 'ACTU{};0'.format(n+1)))
        for cmds in commands:
            cmd_data[cmds[0]] = share.console.parameter.String(cmds[1], read_format='{0}')


