#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Arduino console driver."""

import share


class Arduino(share.console.Base):

    """Communications to SX-750 Arduino console."""

    cmd_data = {
        'VERSION': share.console.ParameterString(
            'VERSION?', read_format='{0}'),
        'DEBUG': share.console.ParameterString(
            '1 DEBUG', read_format='{0}'),
        'QUIET': share.console.ParameterString(
            '0 DEBUG', read_format='{0}'),
        'PGM_5VSB': share.console.ParameterString(
            'PROGRAM-5VSB', read_format='{0}'),
        'PGM_PWRSW': share.console.ParameterString(
            'PROGRAM-PWRSW', read_format='{0}'),
        'OCP_MAX': share.console.ParameterString(
            'OCP-MAX', read_format='{0}'),
        '12_OCP_UNLOCK': share.console.ParameterString(
            '12 OCP-UNLOCK', read_format='{0}'),
        '24_OCP_UNLOCK': share.console.ParameterString(
            '24 OCP-UNLOCK', read_format='{0}'),
        'OCP_STEP_DN': share.console.ParameterString(
            'OCP-STEP-DN', read_format='{0}'),
        'OCP_LOCK': share.console.ParameterString(
            'OCP-LOCK', read_format='{0}'),
        }
