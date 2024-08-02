#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd
"""BC60 console driver."""

import time

import share


class Console(share.console.Base):
    """Communications to console."""

    banner_lines = 8
    cmd_prompt = b"production:>"
    parameter = share.console.parameter
    cmd_data = {
        "SERIAL": parameter.String(
            "production serial",
            read_format="{0}",
            writeable=True,
            write_format="{1} {0}",
        ),
        "PRODUCT-REV": parameter.String(
            "production product-rev",
            read_format="{0}",
            writeable=True,
            write_format="{1} {0}",
        ),
        "HARDWARE-REV": parameter.String(
            "production hw-rev",
            read_format="{0}",
            writeable=True,
            write_format="{1} {0}",
        ),
        "SOFTWARE-REV": parameter.String("production sw-rev", read_format="{0}"),
        "MAC": parameter.String("production mac", read_format="{0}"),
        "OP_MODE": parameter.String(  # "v" = VERIFY_HARDWARE
            "hardware op_mode_set",
            read_format="{0}",
            writeable=True,
            write_format="{1} {0}",
        ),
        "PFC_EN": parameter.Boolean(
            "hardware pfc_en",
            writeable=True,
            write_format="{1} {0}",
        ),
        "DC_EN": parameter.Boolean(
            "hardware dc_dc_en",
            writeable=True,
            write_format="{1} {0}",
        ),
        "OUT_EN": parameter.Boolean(
            "hardware dc_out_sw",
            writeable=True,
            write_format="{1} {0}",
        ),
        "PS_ON": parameter.Boolean(
            "hardware ps_on",
            writeable=True,
            write_format="{1} {0}",
        ),
        "DC_VOLT_SET": parameter.Float(
            "hardware dc_voltage_set",
            readable=False,
            writeable=True,
            write_format="{1} {0}",
            minimum=0.0,
            maximum=16.0,
            scale=1000,
        ),
        "DC_CURRENT_SET": parameter.Float(
            "hardware dc_current_set",
            readable=False,
            writeable=True,
            write_format="{1} {0}",
            minimum=0.0,
            maximum=60.0,
            scale=1000,
        ),
        "PWM_AC_FAN": parameter.Float(
            "hardware pwm_ac_fan",
            readable=False,
            writeable=True,
            write_format="{1} {0}",
            minimum=0.0,
            maximum=100.0,
        ),
        "PWM_DC_FAN": parameter.Float(
            "hardware pwm_dc_fan",
            readable=False,
            writeable=True,
            write_format="{1} {0}",
            write_expected=1,
            minimum=0.0,
            maximum=100.0,
        ),
        "MAINS_VOLT": parameter.Float("hardware mains_det_volts"),
        "MAINS_FREQ": parameter.Float("hardware mains_det_freq", scale=1000),
        "DC_VOLT_MON": parameter.Float("hardware dc_voltage_mon", scale=1000),
        "DC_CURRENT_MON": parameter.Float("hardware dc_current_mon", scale=1000),
    }

    def brand(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '03A'
        @param hardware_rev Hardware revision from ECO eg: '03A'.

        """
        self.action(None, expected=self.banner_lines)
        self["SERIAL"] = sernum
        self["PRODUCT-REV"] = product_rev
        self["HARDWARE-REV"] = hardware_rev

    def startup(self, vset=13.5, ocp=60.0):
        """Start the unit running."""
        vout = 9.0
        self["OP_MODE"] = "v"
        self["PFC_EN"] = True
        self["DC_VOLT_SET"] = vout
        self["DC_CURRENT_SET"] = ocp
        self["DC_EN"] = True
        self["OUT_EN"] = True
        self["PS_ON"] = True
        time.sleep(0.1)
        self["PS_ON"] = False
        self["DC_VOLT_SET"] = vset
