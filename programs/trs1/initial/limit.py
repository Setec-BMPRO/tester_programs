#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trs1 Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Vin', 1, 11.9, 12.1, None, None),
    ('5V', 1, 4.9, 5.1, None, None),
    ('BrakeOff', 1, -0.1, 0.1, None, None),
    ('BrakeOn', 1, 11.9, 12.1, None, None),
    ('LightOff', 1, -0.3, 0.3, None, None),
    ('LightOn', 1, 11.7, 12.3, None, None),
    ('RemoteOff', 1, -0.1, 0.1, None, None),
    ('RemoteOn', 1, 11.9, 12.1, None, None),
    ('GrnLedOn', 1, 0.5, None, None, None),
    ('GrnLedOff', 1, None, 8.0, None, None),
    ('RedLedOn', 1, 0.5, None, None, None),
    ('RedLedOff', 1, None, 8.0, None, None),
    ('Freq1', 1, 0.6, 1.0, None, None),
    ('Freq2', 1, 1.7, 2.7, None, None),
    ('Notify', 2, None, None, None, True),
    )
