#!/usr/bin/env python3
"""BatteryCheck Test Program Limits."""

# Test Limits
DATA = (
    # Serial Number entry
    ('SerNum', 0, None, None, r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$', None),
    # 3.3
    ('3V3', 0, 3.2, 3.4, None, None),
    # 5 +/- 100mV
    ('5VReg', 0, 4.9, 5.1, None, None),
    # 12 +/- 100mV
    ('12VReg', 0, 11.9, 12.1, None, None),
    # Shunt current
    ('shunt', 0, -65.0, -60.0, None, None),
    # Relay
    ('Relay', 0, 100, None, None, None),
    # Programmers
    ('PgmAVR', 0, -0.1, 0.1, None, None),
    ('PgmARM', 0, -0.1, 0.1, None, None),
    # Bluetooth detector
    ('DetectBT', 0, -0.1, 0.1, None, None),
    # ARM Console readings
    ('ARM_SwVer', 0, None, None, r'^1\.4\.3334$', None),
    ('ARM_Volt', 0, 11.5, 12.5, None, None),
    ('ARM_Curr', 0, -65.0, -60.0, None, None),
    ('Batt_Curr_Err', 0, -5.0, 5.0, None, None),
    )
