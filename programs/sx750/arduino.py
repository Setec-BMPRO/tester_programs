#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""SX-750 Arduino console driver."""

import share


class Arduino(share.console.Base):

    """Communications to Arduino console."""

    cmd_data = {
        'VERSION': share.console.parameter.String(
            'VERSION?', read_format='{0}'),
        'DEBUG': share.console.parameter.String(
            '1 DEBUG', read_format='{0}'),
        'QUIET': share.console.parameter.String(
            '0 DEBUG', read_format='{0}'),
        # Programmer commands
        'PGM_5VSB': share.console.parameter.String(
            'PROGRAM-5VSB', read_format='{0}'),
        'PGM_PWRSW': share.console.parameter.String(
            'PROGRAM-PWRSW', read_format='{0}'),
        # 12V/24V OCP commands
        'OCP_MAX': share.console.parameter.String(
            'OCP-MAX', read_format='{0}'),
        '12_OCP_UNLOCK': share.console.parameter.String(
            '12 OCP-UNLOCK', read_format='{0}'),
        '24_OCP_UNLOCK': share.console.parameter.String(
            '24 OCP-UNLOCK', read_format='{0}'),
        'OCP_STEP_DN': share.console.parameter.String(
            'OCP-STEP-DN', read_format='{0}'),
        'OCP_LOCK': share.console.parameter.String(
            'OCP-LOCK', read_format='{0}'),
        }
