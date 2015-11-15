#!/usr/bin/env python3
"""CMR-SBP ALL Test Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Vbat', 1, 11.90, 12.10, None, None),
    ('VbatCharge', 1, 11.8, 12.5, None, None),
    ('Vcc', 1, 3.1, 3.5, None, None),
    ('VErase', 1, 4.8, 5.05, None, None),
    ('IStart', 1, 0.02, None, None, None),
    ('Vchge', 1, 12.8, 15.0, None, None),
    # 2.0A +/- 10mA
    ('Ibat', 1, -2.01, -1.99, None, None),
    ('Final Not Connected', 1, 1.0, None, None, None),
    ('SenseRes', 1, 220, 280, None, None),
    ('Halfcell', 1, 100, 120, None, None),
    ('VChgeOff', 1, 0, 13, None, None),
    ('VChgeOn', 1, 300, 400, None, None),
    ('Bits0+2', 1, 4.5, 5.5, None, None),
    ('Bits1+3', 1, 9.5, 10.5, None, None),
    ('BitsOff', 1, -0.1, 0.1, None, None),
    ('Program', 2, -0.1, 0.1, None, None),
    ('ErrVUncal', 1, -0.5, 0.5, None, None),
    ('ErrIUncal', 1, -0.060, 0.060, None, None),
    # 298K nominal +/- 2.5K in Kelvin (25C +/- 2.5C in Celsius).
    ('BQ-Temp', 1, 295.5, 305.5, None, None),
    ('ErrVCal', 1, -0.03, 0.03, None, None),
    ('ErrICal', 1, -0.015, 0.015, None, None),
    # SerialDate
    ('SerNum', 0, None, None, r'.', None),
    )

DATA_8D = (
    ('VbatIn', 1, 12.8, 15.0, None, None),
    ('ErrV', 1, -0.01, 0.031, None, None),
    ('CycleCnt', 1, 0.5, 20.5, None, None),
    ('RelrnFlg', 1, None, None, None, False),
    ('RotarySw', 1, 255, 257, None, None),
    ('SenseRes', 1, 39.0, 91.0, None, None),
    ('Capacity', 1, 6400.0, 11000.0, None, None),
    ('StateOfCharge', 1, 89.5, 110.5, None, None),
    ('Halfcell', 1, 350.0, 450.0, None, None),
    ('VFCcalStatus', 1, None, None, None, True),
    )

DATA_13F = (
    ('VbatIn', 1, 12.8, 15.0, None, None),
    ('ErrV', 1, -0.01, 0.031, None, None),
    ('CycleCnt', 1, 0.5, 20.5, None, None),
    ('RelrnFlg', 1, None, None, None, False),
    ('RotarySw', 1, 255, 257, None, None),
    ('SenseRes', 1, 221.0, 280.0, None, None),
    ('Capacity', 1, 11000.0, 15000.0, None, None),
    ('StateOfCharge', 1, 89.5, 110.5, None, None),
    ('Halfcell', 1, 350.0, 450.0, None, None),
    ('VFCcalStatus', 1, None, None, None, True),
    )

DATA_17L = (
    ('VbatIn', 1, 12.8, 15.0, None, None),
    ('ErrV', 1, -0.01, 0.031, None, None),
    ('CycleCnt', 1, 0.5, 20.5, None, None),
    ('RelrnFlg', 1, None, None, None, False),
    ('RotarySw', 1, 255, 257, None, None),
    ('SenseRes', 1, 400.0, 460.0, None, None),
    ('Capacity', 1, 15500.0, 20000.0, None, None),
    ('StateOfCharge', 1, 89.5, 110.5, None, None),
    ('Halfcell', 1, 350.0, 450.0, None, None),
    ('VFCcalStatus', 1, None, None, None, True),
    )
