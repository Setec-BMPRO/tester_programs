#!/usr/bin/env python3
"""Trs1 Final Program Limits."""

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Vin', 1, 11.5, 12.5, None, None),
    ('Notify', 2, None, None, None, True),
    )
