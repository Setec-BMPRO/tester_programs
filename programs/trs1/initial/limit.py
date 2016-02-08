#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Vin', 1, 11.0, 12.5, None, None),
    ('PinIn', 1, 11.0, 12.5, None, None),
    ('PinOut', 1, 0.5, None, None, None),
    ('5V', 1, 4.9, 5.1, None, None),
    ('BrakeOff', 1, -0.1, 0.1, None, None),
    ('BrakeOn', 1, 11.9, 12.1, None, None),
    ('LightOff', 1, -0.3, 0.3, None, None),
    ('LightOn', 1, 11.7, 12.3, None, None),
    ('RemoteOff', 1, -0.1, 0.1, None, None),
    ('RemoteOn', 1, 11.9, 12.1, None, None),
    ('RedLedOff', 1, 11.9, 12.1, None, None),
    ('RedLedOn', 1, -0.1, 0.1, None, None),
#    ('GrnLedOff', 1, 11.9, 12.1, None, None),
    ('GrnLedOff', 1, 6.5, 12.1, None, None),
    ('GrnLedOn', 1, -0.1, 0.1, None, None),
    # 0.8 +/- 0.2Hz
    ('Freq1', 1, 0.6, 1.0, None, None),
#    # 2.2 +/- 0.5Hz
#    ('Freq2', 1, 1.7, 2.7, None, None),
    # 1.1 +/- 0.5Hz
    ('Freq2', 1, 0.7, 1.6, None, None),
    ('Notify', 2, None, None, None, True),
    )
