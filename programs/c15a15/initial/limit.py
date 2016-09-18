#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Initial Program Limits."""

from tester.testlimit import lim_hilo, lim_hilo_percent, lim_hi, lim_lo

DATA = (
    lim_hilo('AcMin', 85, 95),
    lim_hilo('VbusMin', 120, 135),
    lim_hilo('VccMin', 7, 14),
    lim_hilo('Ac', 230, 245),
    lim_hilo('Vbus', 330, 350),
    lim_hilo('Vcc', 10, 14),
    lim_hi('LedOn', 6.5),
    lim_lo('LedOff', 0.5),
    lim_hilo_percent('Vout', 15.5, 2.0),
    lim_hilo('OCP_Range', 0.9, 1.4),
    lim_lo('inOCP', 15.2),
    lim_hilo('OCP', 1.05, 1.35),
    lim_hilo('VoutOcp', 5, 16),
    )
