#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Program Limits."""

import os
from tester.testlimit import lim_hilo_delta, lim_hilo_int, lim_boolean

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
CAN_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]

DATA = (
    lim_hilo_delta('Vin', 12.0, 0.5),
    lim_boolean('Notify', True),
    lim_hilo_int('ARM-level1', 1),
    lim_hilo_int('ARM-level2', 2),
    lim_hilo_int('ARM-level3', 3),
    lim_hilo_int('ARM-level4', 4),
    )
