#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Initial Program Limits."""

from testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_percent, lim_lo)

VIN_SET = 30.0      # Input voltage setting
VOUT = 15.5
IOUT_FL = 1.0       # Max output current
OCP_START = 0.9     # OCP measurement parameters
OCP_STOP = 1.3
OCP_STEP = 0.01
OCP_DELAY = 0.5

DATA = (
    lim_hilo_delta('Vin', VIN_SET, 2.0),
    lim_hilo('Vcc', 11.0, 14.0),
    lim_hilo_percent('VoutNL', VOUT, 2.0),
    lim_hilo('VoutFL', VOUT * (1.0 - 0.035), VOUT * (1.0 + 0.02)),
    lim_hilo('VoutOCP', 12.5, VOUT * (1.0 - 0.035)),
    lim_lo('LedOff', 0.5),
    lim_hilo('LedOn', 7.0, 13.5),
    lim_lo('inOCP', 13.6),
    lim_hilo('OCP', 1.03, 1.17),
    )
