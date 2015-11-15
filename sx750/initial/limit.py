#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Initial Test Program Limits."""

# Test Limits
DATA = (
    ('5Voff', 0, -0.5, 0.5, None, None),
    # 5.10 +/- 1.5%
    ('5Vsb_set', 0, 5.034, 5.177, None, None),
    # 5.10 +/- 5.5%
    ('5Vsb', 0, 4.820, 5.380, None, None),
    # Load Reg < 3.0%
    ('5Vsb_reg', 0, 3.0, None, None, None),
    ('12Voff', 0, -0.5, 0.5, None, None),
    # 12.25 +/- 2%
    ('12V_set', 0, 12.005, 12.495, None, None),
    # 12.25 +/- 8%
    ('12V', 0, 11.270, 13.230, None, None),
    # Load Reg < 3.0%
    ('12V_reg', 0, 3.0, None, None, None),
    # Digital Pot setting - counts up from MIN
    ('12V_ocp', 0, 4, 63, None, None),
    # Detect OCP when TP405 > 4V
    ('12V_inOCP', 0, None, 4.0, None, None),
    ('12V_OCPchk', 0, 36.2, 37.0, None, None),
    ('24Voff', 0, -0.5, 0.5, None, None),
    # 24.13 +/- 2%
    ('24V_set', 0, 23.647, 24.613, None, None),
    # 24.13 +/- 10.5%
    ('24V', 0, 21.596, 26.663, None, None),
    # Load Reg < 7.5%
    ('24V_reg', 0, 7.5, None, None, None),
    # Digital Pot setting - counts up from MIN
    ('24V_ocp', 0, 4, 63, None, None),
    # Detect OCP when TP404 > 4V
    ('24V_inOCP', 0, None, 4.0, None, None),
    ('24V_OCPchk', 0, 18.1, 18.5, None, None),
    # 11.4 - 17.0
    ('PriCtl', 0, 11.40, 17.0, None, None),
    ('PGOOD', 0, -0.5, 0.5, None, None),
    ('ACFAIL', 0, 4.5, 5.5, None, None),
    ('ACOK', 0, -0.5, 0.5, None, None),
    ('3V3', 0, 3.2, 3.4, None, None),
    ('ACin', 0, 230, 250, None, None),
    ('ACstart', 0, 85, 90, None, None),
    ('ACstop', 0, 75, 85, None, None),
    ('PFCpre', 0, 400, 440, None, None),
    ('PFCpost', 0, 434, 436, None, None),
    ('OCP12pre', 0, 34, 38, None, None),
    ('OCP12post', 0, 35.7, 36.5, None, None),
    ('OCP12step', 0, 0.116, None, None, None),
    ('OCP24pre', 0, 17, 19, None, None),
    ('OCP24post', 0, 18.1, 18.3, None, None),
    ('OCP24step', 0, 0.058, None, None, None),
    # Data reported by the ARM
    ('ARM-AcDuty', 0, -1, 999, None, None),
    ('ARM-AcPer', 0, -1, 999, None, None),
    ('ARM-AcFreq', 0, -1, 999, None, None),
    ('ARM-AcVolt', 0, -1, 999, None, None),
    ('ARM-PfcTrim', 0, -1, 999, None, None),
    ('ARM-12V', 0, -1, 999, None, None),
    ('ARM-24V', 0, -1, 999, None, None),
    ('ARM-SwVer', 0, None, None, r'^3\.1\.2118$', None),
    ('FixtureLock', 0, 0, 20, None, None),
    # Microswitches on C612, C613, D404
    ('PartCheck', 0, 0, 20, None, None),
    # Snubbing resistors
    ('Snubber', 0, 1000, 3000, None, None),
    # Programming
    ('Program', 0, -0.1, 0.1, None, None),
    )
