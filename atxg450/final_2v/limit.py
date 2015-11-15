#!/usr/bin/env python3
"""ATXG-450-2V Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('5Vsb', 1, 4.845, 5.202, None, None),
    ('5Vsbinocp', 1, 4.70, None, None, None),
    ('5Vsbocp', 1, 2.6, 4.0, None, None),
    ('24Voff', 1, 0.5, None, None, None),
    ('24Von', 1, 23.75, 26.25, None, None),
    ('24Vinocp', 1, 22.8, None, None, None),
    ('24Vocp', 1, 18.0, 24.0, None, None),
    ('12Voff', 1, 0.5, None, None, None),
    ('12Von', 1, 11.685, 12.669, None, None),
    ('12Vinocp', 1, 10.0, None, None, None),
    ('12Vocp', 1, 20.5, 26.0, None, None),
    ('5Voff', 1, 0.5, None, None, None),
    ('5Von', 1, 4.725, 5.4075, None, None),
    ('5Vinocp', 1, 4.75, None, None, None),
    ('5Vocp', 1, 20.5, 26.0, None, None),
    ('3V3off', 1, 0.5, None, None, None),
    ('3V3on', 1, 3.1825, 3.4505, None, None),
    ('3V3inocp', 1, 3.20, None, None, None),
    ('3V3ocp', 1, 17.0, 26.0, None, None),
    ('-12Voff', 1, None, -0.5, None, None),
    ('-12Von', 1, -12.48, -11.52, None, None),
    ('PwrGoodOff', 1, 0.5, None, None, None),
    ('PwrGoodOn', 1, None, 4.5, None, None),
    ('PwrFailOff', 1, None, 4.5, None, None),
    ('PwrFailOn', 1, 0.5, None, None, None),
    ('Notify', 2, None, None, None, True),
    )
