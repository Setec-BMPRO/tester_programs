#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Final Test Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('12V', 0, 11.9, 12.1, None, None),
    ('BTscan', 0, None, None, None, True),
    ('BTpair', 0, None, None, None, True),
    ('ARMSerNum', 0, None, None, None, True),
    ('ARMSwVer', 0, None, None, r'^1\.4\.3334$', None),
    ('SerNum', 0, None, None, r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$', None),
    )
