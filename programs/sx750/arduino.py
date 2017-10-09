#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Arduino console driver."""

from share import console


class Arduino(console.BaseConsole):

    """Communications to SX-750 Arduino console."""

    cmd_data = {
        'VERSION': console.ParameterString(
            'VERSION?', read_format='{0}'),
        'DEBUG': console.ParameterString(
            '1 DEBUG', read_format='{0}'),
        'QUIET': console.ParameterString(
            '0 DEBUG', read_format='{0}'),
        'PGM_5VSB': console.ParameterString(
            'PROGRAM-5VSB', read_format='{0}'),
        'PGM_PWRSW': console.ParameterString(
            'PROGRAM-PWRSW', read_format='{0}'),
        'OCP_MAX': console.ParameterString(
            'OCP-MAX', read_format='{0}'),
        '12_OCP_UNLOCK': console.ParameterString(
            '12 OCP-UNLOCK', read_format='{0}'),
        '24_OCP_UNLOCK': console.ParameterString(
            '24 OCP-UNLOCK', read_format='{0}'),
        'OCP_STEP_DN': console.ParameterString(
            'OCP-STEP-DN', read_format='{0}'),
        'OCP_LOCK': console.ParameterString(
            'OCP-LOCK', read_format='{0}'),
        }
