#!/usr/bin/env python3
"""BC15 Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ACin', 0, 235.0, 245.0, None, None),
    ('Vout', 0, 12.0, 12.9, None, None),
    ('OCP', 0, 32.0, 35.1, None, None),
    ('InOCP', 0, 11.6, None, None, None),
    ('Program', 0, -0.1, 0.1, None, None),
    ('FixtureLock', 0, 1200, None, None, None),
    ('Notify', 1, None, None, None, True),
    # Data reported by the ARM
    ('ARM-SwVer', 0, None, None, r'^1\.0\.10902\.3156$', None),
    ('ARM-AcV', 0, 235.0, 245.0, None, None),
    # Serial Number entry
    ('SerNum', 0, None, None, r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$', None),
    )
