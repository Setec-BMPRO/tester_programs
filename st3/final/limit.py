#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STxx-III Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA20 = (
    ('Voff', 1, 2.0, None, None, None),
    ('Vout', 1, 13.60, 13.70, None, None),
    ('Vbat', 1, 13.40, 13.70, None, None),
    ('Vtrickle', 1, 3.90, 5.70, None, None),
    ('Vboost', 1, 13.80, 14.10, None, None),
    ('FullLoad', 1, 20.1, None, None, None),
    ('LoadOCPramp', 1, 19.5, 28.0, None, None),
    ('LoadOCP', 1, 20.5, 26.0, None, None),
    ('BattOCPramp', 1, 8.0, 13.5, None, None),
    ('BattOCP', 1, 9.0, 11.5, None, None),
    ('inOCP', 1, 11.6, None, None, None),
    ('FuseOut', 1, 0.5, None, None, None),
    ('FuseIn', 1, 13.60, 13.70, None, None),
    ('FuseLabel', 1, None, None, '^ST20\-III$', None),
    ('Notify', 2, None, None, None, True),
    )

DATA35 = (
    ('Voff', 1, 2.0, None, None, None),
    ('Vout', 1, 13.60, 13.70, None, None),
    ('Vbat', 1, 13.40, 13.70, None, None),
    ('Vtrickle', 1, 3.90, 5.70, None, None),
    ('Vboost', 1, 13.80, 14.10, None, None),
    ('FullLoad', 1, 35.1, None, None, None),
    ('LoadOCPramp', 1, 34.1, 43.5, None, None),
    ('LoadOCP', 1, 35.1, 42.5, None, None),
    ('BattOCPramp', 1, 13.0, 19.0, None, None),
    ('BattOCP', 1, 14.0, 17.0, None, None),
    ('inOCP', 1, 11.6, None, None, None),
    ('FuseOut', 1, 0.5, None, None, None),
    ('FuseIn', 1, 13.60, 13.70, None, None),
    ('FuseLabel', 1, None, None, '^ST35\-III$', None),
    ('Notify', 2, None, None, None, True),
    )
