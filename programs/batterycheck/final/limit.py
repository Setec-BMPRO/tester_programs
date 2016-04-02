#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Final Test Program Limits."""

ARM_VERSION = '1.7.4080'        # Software binary version

from testlimit import lim_hilo_delta, lim_string, lim_boolean

DATA = (
    lim_hilo_delta('12V', 12.0, 0.1),
    lim_boolean('BTscan', True),
    lim_boolean('BTpair', True),
    lim_boolean('ARMSerNum', True),
    lim_string('ARMSwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    )
