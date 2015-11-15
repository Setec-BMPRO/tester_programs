#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA12 = (
    ('VoutST', 1, 6.0, 14.0, None, None),
    ('VoutNL', 1, 13.35, 13.75, None, None),
    ('VbatNL', 1, 13.20, 13.75, None, None),
    ('Vout', 1, 12.98, 13.75, None, None),
    ('Vbat', 1, 12.98, 13.75, None, None),
    ('FullLoad', 1, 20.1, None, None, None),
    ('OCPrampLoad', 1, 20.0, 25.5, None, None),
    ('OCPrampBatt', 1, 10.0, 12.5, None, None),
    ('inOCP', 1, 12.98, None, None, None),
    ('OCPLoad', 1, 20.0, 25.0, None, None),
    ('OCPBatt', 1, 10.0, 12.0, None, None),
    ('AlarmOpen', 1, 9000, 11000, None, None),
    ('AlarmClosed', 1, 100, None, None, None),
    ('Notify', 2, None, None, None, True),
    )

DATA24 = (
    ('VoutST', 1, 12.0, 28.0, None, None),
    ('VoutNL', 1, 27.35, 27.85, None, None),
    ('VbatNL', 1, 27.35, 27.85, None, None),
    ('Vout', 1, 26.80, 27.85, None, None),
    ('Vbat', 1, 26.80, 27.85, None, None),
    ('FullLoad', 1, 10.1, None, None, None),
    ('OCPrampLoad', 1, 10.0, 13.5, None, None),
    ('OCPrampBatt', 1, 5.0, 6.5, None, None),
    ('inOCP', 1, 26.80, None, None, None),
    ('OCPLoad', 1, 10.0, 13.0, None, None),
    ('OCPBatt', 1, 5.0, 6.0, None, None),
    ('AlarmOpen', 1, 9000, 11000, None, None),
    ('AlarmClosed', 1, 100, None, None, None),
    ('Notify', 2, None, None, None, True),
    )
