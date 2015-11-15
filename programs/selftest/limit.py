#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ShieldOFF', 1, 5.5, 6.5, None, None),
    ('ShieldON', 1, -0.5, 0.5, None, None),
    ('12V', 1, 11.5, 12.5, None, None),
    ('5V', 1, 4.5, 5.5, None, None),
    ('Dso8', 1, 7.5, 8.5, None, None),
    ('Dso6', 1, 5.5, 6.5, None, None),
    ('Dso4', 1, 3.5, 4.5, None, None),
    ('Dso2', 1, 1.5, 2.5, None, None),
    ('Dcs5', 1, 4.5, 5.5, None, None),
    ('Dcs10', 1, 9.5, 10.5, None, None),
    ('Dcs20', 1, 19.5, 20.5, None, None),
    ('Dcs35', 1, 34.5, 35.5, None, None),
    ('Acs120', 1, 115.0, 125.0, None, None),
    ('Acs240', 1, 235.0, 245.0, None, None),
    ('Dcl05', 1, 0.004, 0.006, None, None),
    ('Dcl10', 1, 0.009, 0.011, None, None),
    ('Dcl20', 1, 0.019, 0.021, None, None),
    ('Dcl40', 1, 0.039, 0.041, None, None),
    ('Rla12V', 1, 11.5, 12.5, None, None),
    ('RlaOff', 1, 11.5, 12.5, None, None),
    ('RlaOn', 1, 0.0, 1.5, None, None),
    ('Disch_on', 1, 9.0, 11.0, None, None),
    ('Disch_off', 1, -0.5, 0.5, None, None),
    )
