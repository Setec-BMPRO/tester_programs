#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Console driver."""

import share


class Console(share.console.SamB11):

    """Communications to BC2 console."""

    parameter = share.console.parameter
    cmd_data = {
        # X-Register values
        'MODEL': parameter.Float('BC2_MODEL', writeable=True),
        'I_ADC_OFFSET': parameter.Float('STC3100_CURRENT_OFFSET', ),
        'SHUNT_RES': parameter.Float('SHUNT_R_NOHMS', ),
        'BATT_V_LSB': parameter.Float('STC3100_VOLTAGE_LSB_UV', ),
        'BATT_V': parameter.Float('VOLTAGE_MV', scale=1000),
        # Calibration commands
        'BATT_V_CAL': parameter.Calibration(
            'STC3100_VOLTAGE_LSB_UV', write_expected=2),
        'ZERO_I_CAL': parameter.Calibration(
            'STC3100_CURRENT_OFFSET', write_expected=2),
        'SHUNT_RES_CAL': parameter.Calibration(
            'SHUNT_R_NOHMS', write_expected=2),
        }
    override_commands = ()


class BTConsole(Console):

    """Bluetooth communications to BC2 console."""

    def _write_command(self, command):
        """Write a command and verify the echo.

        @param command Command string.
        @raises CommandError.

        """
        super().super()._write_command(command)
# TODO: does this call console.Console._write_command
#       or console.BadUart._write_command
