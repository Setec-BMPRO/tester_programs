#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MK7-400-1 Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ACon', 1, 230, 250, None, None),
    ('ACoff', 1, 10, None, None, None),
    ('5V', 1, 4.75, 5.25, None, None),
    ('12Voff', 1, 0.5, None, None, None),
    ('12Von', 1, 12.0, 12.6, None, None),
    ('24Voff', 1, 0.5, None, None, None),
    ('24Von', 1, 23.4, 24.6, None, None),
    ('24V2off', 1, 0.5, None, None, None),
    ('24V2on', 1, 23.4, 24.6, None, None),
    ('PwrFailOff', 1, None, 11.0, None, None),
    ('Notify', 2, None, None, None, True),
    )
