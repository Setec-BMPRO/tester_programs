#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""BC2 Console driver."""

import share


class Console(share.console.SamB11):

    """Communications to BC2 console."""

    parameter = share.console.parameter
    # Shunt resistance value for BatteryCheck100
    shunt_100 = 800000
    cmd_data = {
        share.console.Base.query_last_response: None,
        # X-Register values
        "MODEL": parameter.Float("BC2_MODEL", writeable=True),
        "I_ADC_OFFSET": parameter.Float(
            "STC3100_CURRENT_OFFSET",
        ),
        "SHUNT_RES": parameter.Float("SHUNT_R_NOHMS", maximum=1000000, writeable=True),
        "BATT_V_LSB": parameter.Float(
            "STC3100_VOLTAGE_LSB_UV",
        ),
        "BATT_V": parameter.Float("VOLTAGE_MV", scale=1000),
        "BATT_I": parameter.Float("CURRENT_MA", scale=-1000),
        # Calibration commands
        "BATT_V_CAL": parameter.Calibration("STC3100_VOLTAGE_LSB_UV", write_expected=2),
        "ZERO_I_CAL": parameter.Calibration("STC3100_CURRENT_OFFSET", write_expected=2),
        "SHUNT_RES_CAL": parameter.Calibration("SHUNT_R_NOHMS", write_expected=1),
        # Passkey command
        "PASSKEY": parameter.String(
            "PASSKEY", read_format="{0}?", writeable=True, write_format='"{0} SET-{1}'
        ),
    }
    override_commands = ()

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number.

        @param hw_ver Hardware Version Tuple(Major, Minor, Rev)
        @param sernum Serial Number

        """
        super().brand(hw_ver, sernum)
        self["PASSKEY"] = self.passkey(sernum)
        self["NVWRITE"] = True

    def set_model(self, model):
        """Brand the unit with Hardware ID & Serial Number.

        @param model Model ID (0: '100', 1: '300', 2: 'PRO')

        """
        self["MODEL"] = model
        if model == 0:  # BatteryCheck100 bug - Manual shunt setting
            self["SHUNT_RES"] = self.shunt_100

    @staticmethod
    def passkey(sernum):
        """Calculate the Passkey from the Serial Number.

        @param sernum Serial Number
        @return 6 digit passkey

        """
        hash_start, hash_mult = 56210, 29
        hash = hash_start
        for char in sernum[::-1]:
            hash = ((hash * hash_mult) & 0xFFFFFF) ^ ord(char)
        hash = hash % 1000000
        return "{0:06}".format(hash)
