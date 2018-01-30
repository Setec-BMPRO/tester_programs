#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Console driver."""

import share


class Console(share.console.SamB11):

    """Communications to BC2 console."""

    parameter = share.console.parameter
    cmd_data = {
        share.console.Base.query_last_response: None,
        # X-Register values
        'MODEL': parameter.Float('BC2_MODEL', writeable=True),
        'I_ADC_OFFSET': parameter.Float('STC3100_CURRENT_OFFSET', ),
        'SHUNT_RES': parameter.Float('SHUNT_R_NOHMS', ),
        'BATT_V_LSB': parameter.Float('STC3100_VOLTAGE_LSB_UV', ),
        'BATT_V': parameter.Float('VOLTAGE_MV', scale=1000),
        'BATT_I': parameter.Float('CURRENT_MA', scale=1000),
        # Calibration commands
        'BATT_V_CAL': parameter.Calibration(
            'STC3100_VOLTAGE_LSB_UV', write_expected=1),
        'ZERO_I_CAL': parameter.Calibration(
            'STC3100_CURRENT_OFFSET', write_expected=1),
        'SHUNT_RES_CAL': parameter.Calibration(
            'SHUNT_R_NOHMS', write_expected=1),
        }
    override_commands = ()
