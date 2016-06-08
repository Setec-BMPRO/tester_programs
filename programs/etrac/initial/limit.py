#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ETrac-II Initial Program Limits."""

PIC_HEX = 'etracII-2A.hex'

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Vin', 1, 12.9, 13.1, None, None),
    ('Vin2', 1, 10.8, 12.8, None, None),
    ('5V', 1, 4.95, 5.05, None, None),
    ('5Vusb', 1, 4.75, 5.25, None, None),
    ('Vbat', 1, 8.316, 8.484, None, None),
    )
