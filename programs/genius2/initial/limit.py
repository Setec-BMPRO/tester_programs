#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GENIUS-II and GENIUS-II-H Initial Test Program Limits."""

PIC_HEX = 'genius2_2.hex'

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('VbatCtl', 1, 12.7, 13.1, None, None),
    ('Vdd', 1, 4.90, 5.10, None, None),
    ('Vout', 1, 13.60, 13.70, None, None),
    ('Vbat', 1, 13.60, 13.70, None, None),
    ('Vaux', 1, 13.60, 13.80, None, None),
    ('FlyLead', 1, 20.0, 40.0, None, None),
    ('AcIn', 1, 235.0, 245.0, None, None),
    ('Vbus', 1, 310.0, 350.0, None, None),
    ('Vcc', 1, 13.8, 22.5, None, None),
    ('VoutPre', 1, 12.5, 15.0, None, None),
    ('Vctl', 1, 11.5, 12.5, None, None),
    ('MaxBattLoad', 1, 15.0, None, None, None),
    ('InOCP', 1, 13.24, None, None, None),
    ('OCP', 1, 34.0, 43.0, None, None),
    ('Notify', 2, None, None, None, True),
    ('FixtureLock', 0, 20, None, None, None),
    )

DATA_H = (
    ('VbatCtl', 1, 12.7, 13.1, None, None),
    ('Vdd', 1, 4.90, 5.10, None, None),
    ('Vout', 1, 13.60, 13.70, None, None),
    ('Vbat', 1, 13.60, 13.70, None, None),
    ('Vaux', 1, 13.60, 13.80, None, None),
    ('FlyLead', 1, 20.0, 40.0, None, None),
    ('AcIn', 1, 235.0, 245.0, None, None),
    ('Vbus', 1, 310.0, 350.0, None, None),
    ('Vcc', 1, 13.8, 22.5, None, None),
    ('VoutPre', 1, 12.5, 15.0, None, None),
    ('Vctl', 1, 11.5, 12.5, None, None),
    ('MaxBattLoad', 1, 30.0, None, None, None),
    ('InOCP', 1, 13.24, None, None, None),
    ('OCP', 1, 34.0, 43.0, None, None),
    ('Notify', 2, None, None, None, True),
    ('FixtureLock', 0, 20, None, None, None),
    )
