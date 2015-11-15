#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE4 & BCE5 Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA4 = (
    ('VoutNL', 1, 13.50, 13.80, None, None),
    ('Vout', 1, 13.28, 13.80, None, None),
    ('Vbat', 1, 13.28, 13.92, None, None),
    ('FullLoad', 1, 10.1, None, None, None),
    ('OCPramp', 1, 10.0, 13.5, None, None),
    ('inOCP', 1, 13.28, None, None, None),
    ('OCP', 1, 10.2, 13.0, None, None),
    ('AlarmOpen', 1, 9.0, 11.0, None, None),
    ('AlarmClosed', 1, 1.0, None, None, None),
    ('InDropout', 1, 13.28, None, None, None),
    ('Dropout', 1, 150.0, 180.0, None, None),
    )

DATA5 = (
    ('VoutNL', 1, 27.00, 27.60, None, None),
    ('Vout', 1, 26.56, 27.84, None, None),
    ('Vbat', 1, 26.56, 27.84, None, None),
    ('FullLoad', 1, 5.1, None, None, None),
    ('OCPramp', 1, 5.0, 7.0, None, None),
    ('inOCP', 1, 26.56, None, None, None),
    ('OCP', 1, 5.1, 6.3, None, None),
    ('AlarmOpen', 1, 9.0, 11.0, None, None),
    ('AlarmClosed', 1, 1.0, None, None, None),
    ('InDropout', 1, 26.56, None, None, None),
    ('Dropout', 1, 150.0, 180.0, None, None),
    )
