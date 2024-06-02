#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd.
"""TRS-BTx Configuration."""


def get(parameter):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @return configuration class

    """
    config = {
        "BT2": TrsBt2,
        "BTS": TrsBts,
    }[parameter]
    return config


class TrsBt2:
    """TRS-BT2 configuration."""

    sw_image = "trs-bts_factory_2.0.20494.2194.hex"
    hw_version = (4, 0, "A")


class TrsBts:
    """TRS-BTS configuration."""

    sw_image = TrsBt2.sw_image
    hw_version = (5, 0, "A")
