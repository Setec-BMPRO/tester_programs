#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Final Program Limits."""

import os

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

NEW_PSU  =  False

HW_REV = '06A'

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('TecOff', 1, -1.5, 1.5, None, None),
    ('TecVmonOff', 1, -1.5, 1.5, None, None),
    ('LddOff', 1, -1.5, 1.5, None, None),
    ('IsVmonOff', 1, -1.5, 1.5, None, None),
    ('15VOff', 1, -1.5, 1.5, None, None),
    ('-15VOff', 1, -1.5, 1.5, None, None),
    ('15VpOff', 1, -1.5, 1.5, None, None),
    ('15VpSwOff', 1, -1.5, 1.5, None, None),
    ('5VOff', 1, -1.5, 1.5, None, None),
    ('15V', 1, 14.25, 15.75, None, None),
    ('-15V', 1, -15.75, -14.25, None, None),
    ('15Vp', 1, 14.25, 15.75, None, None),
    ('15VpSw', 1, 14.25, 15.75, None, None),
    ('5V', 1, 4.85, 5.10, None, None),
    ('Tec', 1, 14.70, 15.30, None, None),
    ('TecPhase', 1, -15.30, -14.70, None, None),
    ('TecVset', 1, 4.95, 5.05, None, None),
    ('TecVmon0V', 1, -0.5, 0.5, None, None),
    ('TecVmon', 1, 4.90, 5.10, None, None),
    ('TecErr', 1, -0.275, 0.275, None, None),
    ('TecVmonErr', 1, -0.030, 0.030, None, None),
    ('IsVmon', 1, -0.4, 2.5, None, None),
    ('IsOut0V', 1, -0.001, 0.001, None, None),
    ('IsOut06V', 1, 0.005, 0.007, None, None),
    ('IsOut5V', 1, 0.048, 0.052, None, None),
    ('IsIout0V', 1, -0.05, 0.05, None, None),
    ('IsIout06V', 1, 0.58, 0.62, None, None),
    ('IsIout5V', 1, 4.90, 5.10, None, None),
    ('IsSet06V', 1, 0.55, 0.65, None, None),
    ('IsSet5V', 1, 4.95, 5.05, None, None),
    ('SetMonErr', 1, -0.07, 0.07, None, None),
    ('SetOutErr', 1, -0.07, 0.07, None, None),
    ('MonOutErr', 1, -0.07, 0.07, None, None),
    ('SerEntry', 0, None, None, r'^[AS][0-9]{4}[0-9,A-Z]{2}[0-9]{4}$', None),
    ('HwRev', 0, None, None, r'.', None),
    ('SerChk', 0, None, None, r'.', None),
    ('Notify', 2, None, None, None, True),
    )
