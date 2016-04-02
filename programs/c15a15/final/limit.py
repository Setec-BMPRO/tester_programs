#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Final Program Limits."""

from testlimit import lim_hilo, lim_lo, lim_boolean

DATA = (
    lim_hilo('Vout', 15.2, 15.8),
    lim_lo('Voutfl', 5.0),
    lim_hilo('OCP', 0.0, 0.4),
    lim_lo('inOCP', 13.6),
    lim_boolean('Notify', True),
    )
