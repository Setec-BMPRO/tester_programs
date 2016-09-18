#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Final Program Limits."""

from tester.testlimit import lim_hilo, lim_hilo_percent, lim_lo, lim_boolean

DATA = (
    lim_hilo_percent('Vout', 15.0, 2.0),
    lim_lo('Voutfl', 5.0),
    lim_hilo('OCP', 0.0, 0.4),  # Adds to a resistor load!
    lim_lo('inOCP', 13.6),
    lim_boolean('Notify', True),
    )
