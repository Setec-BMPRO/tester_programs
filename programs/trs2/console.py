#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Console driver."""

import share


class Console(share.console.SamB11):

    """Communications to TRS2 console."""

    parameter = share.console.parameter
    cmd_data = {
        # X-Register values
        'VBATT': parameter.Hex('TRS2_BATT_MV', scale=1000),
        'VBRAKE': parameter.Hex('TRS2_BRAKE_MV', scale=1000),
        'IBRAKE': parameter.Hex('TRS2_BRAKE_MA', scale=1000),
        'VPIN': parameter.Hex('TRS2_DROP_ACROSS_PIN_MV', scale=1000),
        'FAULT_CODE': parameter.Hex(
            'TRS2_FAULT_CODE_BITS', minimum=0, maximum=0x3),
        # Calibration commands
        'VBRAKE_OFFSET': parameter.Calibration(
            'BRAKEV_OFF_SET', write_expected=2),
        'VBRAKE_GAIN': parameter.Calibration(
            'BRAKEV_GAIN_SET', write_expected=2),
        # OverrideTo commands
        'BR_LIGHT': parameter.Override('TRS2_BRAKE_LIGHT_EN_OVERRIDE'),
        'MONITOR': parameter.Override('TRS2_MONITOR_EN_OVERRIDE'),
        'RED_LED': parameter.Override('TRS2_RED_LED_OVERRIDE'),
        'GREEN_LED': parameter.Override('TRS2_GREEN_LED_OVERRIDE'),
        'BLUE_LED': parameter.Override('TRS2_BLUE_LED_OVERRIDE'),
        'BLUETOOTH': parameter.Override('TRS2_BLUETOOTH_EN_OVERRIDE'),
        }
    override_commands = (
        'BR_LIGHT', 'MONITOR', 'RED_LED', 'GREEN_LED', 'BLUE_LED')


class BTConsole(Console):

    """Bluetooth communications to BC2 console."""

    def _write_command(self, command):
        """Write a command and verify the echo.

        Overrides _write_command() of BadUart console.
        @param command Command string.
        @raises CommandError.

        """
        # Uses _write_command() of Base console.
        super(share.console.BadUart, self)._write_command(command)
