#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""RvView/JDisplay Configuration."""


def get(parameter):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @return configuration class

    """
    return {
        "JD": JDisplay,
        "RV": RvView,
        "RV2": RvView2,
        "RV2A": RvView2a,
    }[parameter]


class JDisplay:
    """JDisplay configuration."""

    sw_file = "JDisplay_1.0.17318.27.bin"
    hw_version = (3, 0, "A")
    is_atsam = False


class RvView:
    """RvView configuration."""

    sw_file = "RvView_1.1.16188.1004.bin"
    hw_version = (3, 0, "A")
    is_atsam = False


class RvView2:
    """RvView2 NXP micro configuration."""

    sw_file = "RvView2_1.2.20314.1010.bin"
    hw_version = (1, 0, "A")
    is_atsam = False


class RvView2a:
    """RvView2 ATSAMC21 micro configuration."""

    sw_file = "RvView2a_1.4.0-0-gae44ae2.bin"
    is_atsam = True
