#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C45A-15 Initial Program Limits."""

PIC_HEX = 'c45a-15.hex'

OCP_PERCENT_REG = 0.015

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('VacStart', 1, 92.0, 98.0, None, None),
    ('Vac', 1, 238.0, 242.0, None, None),
    ('Vbus', 1, 330.0, 350.0, None, None),
    ('Vcc', 1, 9.5, 15.0, None, None),
    ('SecBiasIn', 1, 11.9, 12.1, None, None),
    ('Vref', 1, 4.9, 5.1, None, None),
    ('VrefOff', 1, 1.0, None, None, None),
    ('VoutPreExt', 1, 11.9, 12.1, None, None),
    ('VoutExt', 1, 11.9, 12.1, None, None),
    ('VoutPre', 1, 11.9, 12.1, None, None),
    ('VoutLow', 1, 8.55, 9.45, None, None),
    ('Vout', 1, 15.2, 16.8, None, None),
    ('VsenseLow', 1, 8.2, 10.0, None, None),
    ('VsenseOn', 1, 11.8, 12.1, None, None),
    ('VsenseOff', 1, 1.0, None, None, None),
    ('GreenOn', 1, 1.8, 2.2, None, None),
    ('YellowOn', 1, 1.6, 2.2, None, None),
    ('RedOn', 1, 4.0, 5.5, None, None),
    ('RedFlash', 1, 2.0, 2.75, None, None),
    ('LedOff', 1, 0.2, None, None, None),
    ('inOVP', 1, 6.5, None, None, None),
    ('OVP', 1, 18.0, 21.0, None, None),
    ('Reg', 1, -1.5, 0, None, None),
    ('inOCP', 1, 1e6, None, None, None),
    ('OCP', 1, 2.85, 3.15, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Program', 2, -0.1, 0.1, None, None),
    ('Notify', 2, None, None, None, True),
    )
