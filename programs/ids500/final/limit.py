#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Final Program Limits."""

import os
from tester.testlimit import lim_lo, lim_hilo, lim_string, lim_boolean

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    lim_lo('TecOff', 1.5),
    lim_lo('TecVmonOff', 1.5),
    lim_lo('LddOff', 1.5),
    lim_lo('IsVmonOff', 1.5),
    lim_lo('15VOff', 1.5),
    lim_lo('-15VOff', 1.5),
    lim_lo('15VpOff', 1.5),
    lim_lo('15VpSwOff', 1.5),
    lim_lo('5VOff', 1.5),
    lim_hilo('15V', 14.25, 15.75),
    lim_hilo('-15V', -15.75, -14.25),
    lim_hilo('15Vp', 14.25, 15.75),
    lim_hilo('15VpSw', 14.25, 15.75),
    lim_hilo('5V', 4.85, 5.10),
    lim_hilo('Tec', 14.70, 15.30),
    lim_hilo('TecPhase', -15.30, -14.70),
    lim_hilo('TecVset', 4.95, 5.05),
    lim_lo('TecVmon0V', 0.5),
    lim_hilo('TecVmon', 4.90, 5.10),
    lim_hilo('TecErr', -0.275, 0.275),
    lim_hilo('TecVmonErr', -0.030, 0.030),
    lim_hilo('IsVmon', -0.4, 2.5),
    lim_hilo('IsOut0V', -0.001, 0.001),
    lim_hilo('IsOut06V', 0.005, 0.007),
    lim_hilo('IsOut5V', 0.048, 0.052),
    lim_hilo('IsIout0V', -0.05, 0.05),
    lim_hilo('IsIout06V', 0.58, 0.62),
    lim_hilo('IsIout5V', 4.90, 5.10),
    lim_hilo('IsSet06V', 0.55, 0.65),
    lim_hilo('IsSet5V', 4.95, 5.05),
    lim_hilo('SetMonErr', -0.07, 0.07),
    lim_hilo('SetOutErr', -0.07, 0.07),
    lim_hilo('MonOutErr', -0.07, 0.07),
    lim_string('HwRev', r'^[0-9]{2}[AB]$'),
    lim_string('SerNum', r'^[AS][0-9]{4}[0-9,A-Z]{2}[0-9]{4}$'),
    lim_boolean('Notify', True),
    )
