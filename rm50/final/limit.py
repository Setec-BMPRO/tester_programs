#!/usr/bin/env python3
"""RM-50-24 Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Rsense', 1, 980, 1020, None, None),
    ('Vsense', 1, 0.0001, None, None, None),
    ('uSwitch', 0, 0, 100, None, None),
    ('Vdrop', 1, 0.4, None, None, None),
    ('24Vdcin', 1, 23.0, 24.4, None, None),
    ('24Vdcout', 1, 23.6, 24.4, None, None),
    ('24Voff', 1, 1.0, None, None, None),
    ('24Vnl', 1, 23.6, 24.4, None, None),
    ('24Vfl', 1, 23.4, 24.1, None, None),
    ('24Vpl', 1, 23.0, 24.1, None, None),
    ('OCP', 1, 3.2, 4.3, None, None),
    ('inOCP', 1, 23.0, None, None, None),
    ('CurrShunt', 1, 2.5, None, None, None),
    ('PowNL', 1, 1.0, 5.0, None, None),
    ('PowFL', 1, 40.0, 70.0, None, None),
    ('Eff', 1, None, 84.0, None, None),
    ('Notify', 2, None, None, None, True),
    )
