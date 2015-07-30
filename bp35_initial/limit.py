#!/usr/bin/env python3
"""BP35 Initial Program Limits."""

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('ACin', 0, 235.0, 245.0, None, None),
    ('Vpfc', 0, 401.0, 424.0, None, None),
    ('12Vpri', 0, 11.5, 13.0, None, None),
    ('5Vusb', 0, -4.5, 5.5, None, None),
    ('15Vs', 0, 11.5, 13.0, None, None),
    # 12.8 +/- 0.1
    ('Vout', 0, 12.3, 12.9, None, None),
    # 12.8 +/- 5%
    ('VoutFl', 0, 12.16, 13.44, None, None),
    ('VoutOff', 0, 0.5, None, None, None),
    ('VbatIn', 0, 11.5, 12.5, None, None),
    ('Vbat', 0, 12.6, 13.0, None, None),
    ('Vaux', 0, 12.6, 13.0, None, None),
    ('3V3', 0, 3.25, 3.35, None, None),
    ('FanOn', 0, 12.0, 13.0, None, None),
    ('FanOff', 0, 0.5, None, None, None),
    ('3V3prog', 0, 3.2, 3.4, None, None),
    ('OutOCP', 0, 32.0, 35.1, None, None),
    ('BatOCP', 0, 6.0, 9.0, None, None),
    ('InOCP', 0, 11.6, None, None, None),
    ('Program', 0, -0.1, 0.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('SwShort', 0, None, 20, None, None),
    ('Notify', 1, None, None, None, True),
    # Data reported by the ARM
    ('ARM-SwVer', 0, None, None, r'^1\.0\.10902\.3156$', None),
    ('ARM-AcV', 0, 235.0, 245.0, None, None),
    ('ARM-AcF', 0, 49.0, 51.0, None, None),
    ('ARM-PriT', 0, 8.0, 50.0, None, None),
    ('ARM-SecT', 0, 8.0, 50.0, None, None),
    ('ARM-Vout', 0, 12.0, 12.9, None, None),
    ('ARM-Fan', 0, 0, 100, None, None),
    ('ARM-LoadI', 0, 0.1, 12.1, None, None),
    ('ARM-BattI', 0, 3.0, 5.0, None, None),
    ('ARM-AuxV', 0, 12.3, 12.9, None, None),
    ('ARM-AuxI', 0, 0.05, 0.4, None, None),
    # Serial Number entry
    ('SerNum', 0, None, None, r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$', None),
    ('CAN_ID', 0, None, None, r'^RRQ,32,0', None),
    ('CAN_BIND', 0, _CAN_BIND - 0.5, _CAN_BIND + 0.5, None, None),
    ('CAN_STATS', 0, -0.5, 0.5, None, None),
    )
