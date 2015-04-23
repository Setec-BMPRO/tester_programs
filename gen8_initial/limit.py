#!/usr/bin/env python3
"""GEN8 Initial Test Program Limits."""

# Test Limits
DATA = (
    ('5Voff', 0, 0.5, None, None, None),
    # 5.10 +/- 1.0%
    ('5Vset', 0, 5.049, 5.151, None, None),
    # 5.10 +/- 2.0%
    ('5V', 0, 4.998, 5.202, None, None),
    ('12Voff', 0, 0.5, None, None, None),
    # 12.1 +/- 1V
    ('12Vpre', 0, 11.1, 13.1, None, None),
    # 12.18 +/- 0.01V
    ('12Vset', 0, 12.17, 12.19, None, None),
    # 12.18 +/- 2.5%
    ('12V', 0, 11.8755, 12.4845, None, None),
    ('12V2off', 0, 0.5, None, None, None),
    # 12.0 +/- 1V
    ('12V2pre', 0, 11.0, 12.0, None, None),
    # 12.18 +2.5% -3.0%
    ('12V2', 0, 11.8146, 12.4845, None, None),
    ('24Voff', 0, 0.5, None, None, None),
    # 24V +/- 2.0V (TestEng estimate)
    ('24Vpre', 0, 22.0, 26.0, None, None),
    # 24.0 +7% -5%
    ('24V', 0, 22.80, 25.68, None, None),
    # 3.30 +/- 10% (TestEng estimate)
    ('3V3', 0, 3.0, 3.6, None, None),
    ('PWRFAIL', 0, 0.5, None, None, None),
    ('InputFuse', 0, 230, 250, None, None),
    ('12Vpri', 0, 11.4, 17.0, None, None),
    ('PFCpre', 0, 420, 450, None, None),
    ('PFCpost1', 0, 439.3, 440.8, None, None),
    ('PFCpost2', 0, 439.3, 440.8, None, None),
    ('PFCpost3', 0, 439.3, 440.8, None, None),
    ('PFCpost4', 0, 439.3, 440.8, None, None),
    ('PFCpost', 0, 439.1, 440.9, None, None),
    # Data reported by the ARM
    ('ARM-AcDuty', 0, 0, 100, None, None),
    ('ARM-AcPer', 0, 0, 100, None, None),
    ('ARM-AcFreq', 0, 40, 60, None, None),
    ('ARM-AcVolt', 0, 0, 300, None, None),
    ('ARM-PfcTrim', 0, 0, 100, None, None),
    ('ARM-12VTrim', 0, 0, 100, None, None),
    ('ARM-5V', 0, 4.0, 6.0, None, None),
    ('ARM-12V', 0, 11.0, 13.0, None, None),
    ('ARM-24V', 0, 22.0, 26.0, None, None),
    ('ARM-SwVer', 0, None, None, r'^1\.4\.645$', None),
    ('ARM-5Vadc', 0, 0, 999999, None, None),
    ('ARM-12Vadc', 0, 0, 999999, None, None),
    ('ARM-24Vadc', 0, 0, 999999, None, None),
    # Microswitches on C106, C107, D2
    ('PartCheck', 0, 20, None, None, None),
    # Solder bridge on fan connector
    ('FanShort', 0, None, 20, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    # Programming (0 == Pass, 1 == Fail)
    ('Program', 0, -0.1, 0.1, None, None),
    )
