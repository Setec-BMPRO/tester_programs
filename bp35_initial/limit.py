#!/usr/bin/env python3
"""BP35 Initial Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ACin', 1, 235.0, 245.0, None, None),
    ('Vbus', 1, 410.0, 420.0, None, None),
    ('12Vpri', 1, 11.5, 13.0, None, None),
    ('5Vusb', 1, -4.5, 5.5, None, None),
    ('15Vs', 1, 11.5, 13.0, None, None),
    # 12.8 +/- 0.1
    ('Vout', 1, 12.7, 12.9, None, None),
    # 12.8 +/- 5%
    ('VoutFl', 1, 12.16, 13.44, None, None),
    ('VoutOff', 1, 0.5, None, None, None),
    ('Vbat', 1, 12.6, 13.0, None, None),
    ('3V3', 1, 3.25, 3.35, None, None),
    ('FanOn', 1, 11.5, 12.5, None, None),
    ('FanOff', 1, 0.5, None, None, None),
    ('3V3prog', 1, 3.2, 3.4, None, None),
    ('OutOCP', 1, 32.0, 35.0, None, None),
    ('BatOCP', 1, 18.5, 20.0, None, None),
    ('InOCP', 1, 11.6, None, None, None),
    ('Program', 2, -0.1, 0.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('SwShort', 0, None, 20, None, None),
    ('Notify', 2, None, None, None, True),
    ('ARM-SwVer', 0, None, None, r'^1\.0\.3119$', None),
    # Serial Number entry
    ('SerNum', 0, None, None, r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$', None),
    )
