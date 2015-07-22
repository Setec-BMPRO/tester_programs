#!/usr/bin/env python3
"""Trek2 Initial Program Limits."""

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Vin', 1, 11.5, 12.5, None, None),
    # 3.3 +/- 3%
    ('3V3', 1, 3.25, 3.35, None, None),
    ('BkLghtOff', 1, 0.5, None, None, None),
    # 40mA = 4V with 100R (1%)
    ('BkLghtOn', 1, 3.465, 4.545, None, None),
    ('Program', 2, -0.1, 0.1, None, None),
    # Serial Number entry
    ('SerNum', 0, None, None, r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$', None),
    ('CAN_ID', 0, None, None, r'^RRQ,16,0', None),
    ('CAN_BIND', 0, _CAN_BIND - 0.5, _CAN_BIND + 0.5, None, None),
    ('SwVer', 0, None, None, r'^1\.0\.10892\.112$', None),
    ('Notify', 2, None, None, None, True),
    )
