#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Configuration."""

# Injected AUX voltage
vaux = 12.8
vsol = 14.6

# Software image filename
sw_image = 'mb3_2.0.hex'

# ATTiny406 fuse settings
#   FuseName: (FuseNumber, FuseValue)
fuses = {
    'APPEND': (0x07, 0x00),
    'BODCFG': (0x01, 0x00),
    'BOOTEND': (0x08, 0x00),
    'OSCCFG': (0x02, 0x02),
    'SYSCFG0': (0x05, 0xf7),
    'SYSCFG1': (0x06, 0x07),
    'WDTCFG': (0x00, 0x00),
    }
