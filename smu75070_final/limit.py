#!/usr/bin/env python3
"""SMU750-70 Final Program Limits."""

# Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('70VOn', 1, 69.3, 70.7, None, None),
    ('70VOff', 1, -0.5, 69.2, None, None),
    ('OCP', 1, 11.3, 11.6, None, None),
    ('inOCP', 1, 69.3, None, None, None),
    ('Notify', 2, None, None, None, True),
    )
