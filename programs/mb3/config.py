#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Configuration."""

# Injected AUX voltage
vaux = 12.8
# Injected SOLAR voltage
vsol = 14.6

# Software image filename
sw_image = "mb3_v2.6-0-gb0c92b4.hex"

# ATTiny406 fuse settings
#   FuseName: (FuseNumber, FuseValue)
fuses = {
    "APPEND": (0x07, 0x00),
    "BODCFG": (0x01, 0x00),
    "BOOTEND": (0x08, 0x00),
    "OSCCFG": (0x02, 0x02),
    "SYSCFG0": (0x05, 0xFB),
    "SYSCFG1": (0x06, 0x07),
    "WDTCFG": (0x00, 0x00),
}
