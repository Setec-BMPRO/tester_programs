#!/usr/bin/env python3
"""Drifter(BM) Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
_COMMON = (
    ('SwOff', 1, 1.0, None, None, None),
    ('SwOn', 1, None, 10.0, None, None),
    ('USB5V', 1, 4.75, 5.25, None, None, None),
    ('Notify', 2, None, None, None, True),
    )

DATA = _COMMON
DATA_BM = _COMMON
