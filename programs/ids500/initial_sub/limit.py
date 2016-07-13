#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Program Limits."""

import os

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]

PIC_HEX_MIC = 'ids_picMic_2.hex'
PIC_HEX_SYN = 'ids_picSyn_2.hex'

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA_MIC = (
    ('5V', 1, 4.95, 5.05, None, None),
    ('Comms', 1, None, None, r'.', None),
    ('SwRev', 1, 1.5, 2.5, None, None),
    ('MicroTemp', 1, 8.0, 30.0, None, None),
    ('Program', 2, -0.1, 0.1, None, None),
    )

DATA_AUX = (
    ('5V', 1, 4.95, 5.05, None, None),
    ('5VOff', 1, 0.5, None, None, None),
    ('15VpOff', 1, 0.5, None, None, None),
    ('15Vp', 1, 14.25, 15.75, None, None),
    ('15VpSwOff', 1, 0.5, None, None, None),
    ('15VpSw', 1, 14.25, 15.75, None, None),
    ('20VL', 1, 18.0, 25.0, None, None),
    ('-20V', 1, -25.0, -18.0, None, None),
    ('15V', 1, 14.25, 15.75, None, None),
    ('-15V', 1, -15.75, -14.25, None, None),
    ('PwrGoodOff', 1, 0.5, None, None, None),
    ('PwrGood', 1, 4.8, 5.1, None, None),
    ('ACurr_5V_1', 1, -0.1, 0.1, None, None),
    ('ACurr_5V_2', 1, 1.76, 2.15, None, None),
    ('ACurr_15V_1', 1, -0.1, 0.13, None, None),
    ('ACurr_15V_2', 1, 1.16, 1.42, None, None),
    ('AuxTemp', 1, 2.1, 4.3, None, None),
    ('InOCP5V', 1, 4.8, None, None, None),
    ('InOCP15Vp', 1, 14.2, None, None, None),
    ('OCP', 1, 7.0, 10.0, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    )

DATA_BIAS = (
    ('400V', 1, 390, 410, None, None),
    ('PVcc', 1, 12.8, 14.5, None, None),
    ('12VsbRaw', 1, 12.7, 13.49, None, None),
    ('OCP Trip', 1, 12.6, None, None, None),
    ('InOCP', 1, 12.6, None, None, None),
    ('OCP', 1, 1.2, 2.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    )

DATA_BUS = (
    ('400V', 1, 390, 410, None, None),
    ('20VT_load0_out', 1, 22.0, 24.0, None, None),
    ('9V_load0_out', 1, 10.8, 12.0, None, None),
    ('20VL_load0_out', 1, 22.0, 24.0, None, None),
    ('-20V_load0_out', 1, -25.0, -22.0, None, None),
    ('20VT_load1_out', 1, 22.0, 25.0, None, None),
    ('9V_load1_out', 1, 9.0, 11.0, None, None),
    ('20VL_load1_out', 1, 22.0, 25.0, None, None),
    ('-20V_load1_out', 1, -26.0, -22.0, None, None),
    ('20VT_load2_out', 1, 19.0, 24.0, None, None),
    ('9V_load2_out', 1, 9.0, 11.0, None, None),
    ('20VL_load2_out', 1, 19.0, 21.5, None, None),
    ('-20V_load2_out', 1, -22.2, -20.0, None, None),
    ('20VT_load3_out', 1, 17.5, 20.0, None, None),
    ('9V_load3_out', 1, 9.0, 12.0, None, None),
    ('20VL_load3_out', 1, 22.0, 24.0, None, None),
    ('-20V_load3_out', 1, -26.0, -22.0, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    )

DATA_SYN = (
    ('20VT', 1, 18.5, 22.0, None, None),
    ('-20V', 1, -22.0, -18.0, None, None),
    ('9V', 1, 8.0, 11.0, None, None),
    ('TecOff', 1, -0.5, 0.5, None, None),
    ('Tec0V', 1, -0.5, 1.0, None, None),
    ('Tec2V5', 1, 7.3, 7.8, None, None),
    ('Tec5V', 1, 14.75, 15.5, None, None),
    ('Tec5V_Rev', 1, -15.5, -14.5, None, None),
    ('LddOff', 1, -0.5, 0.5, None, None),
    ('Ldd0V', 1, -0.5, 0.5, None, None),
    ('Ldd0V6', 1, 0.6, 1.8, None, None),
    ('Ldd5V', 1, 1.0, 2.5, None, None),
    ('LddVmonOff', 1, -0.5, 0.5, None, None),
    ('LddImonOff', 1, -0.5, 0.5, None, None),
    ('LddImon0V', 1, -0.05, 0.05, None, None),
    ('LddImon0V6', 1, 0.55, 0.65, None, None),
    ('LddImon5V', 1, 4.9, 5.1, None, None),
    ('ISIout0A', 1, -1.0, 1.0, None, None),
    ('ISIout6A', 1, 5.0, 7.0, None, None),
    ('ISIout50A', 1, 49.0, 51.0, None, None),
    ('ISIset5V', 1, 4.95, 5.05, None, None),
    ('AdjLimits', 1, 49.9, 50.1, None, None),
    ('TecVmonOff', 1, -0.5, 0.5, None, None),
    ('TecVmon0V', 1, -0.5, 0.8, None, None),
    ('TecVmon2V5', 1, 2.4375, 2.5625, None, None),
    ('TecVmon5V', 1, 4.925, 5.075, None, None),
    ('TecVsetOff', 1, -0.5, 0.5, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Notify', 2, None, None, None, True),
    )

