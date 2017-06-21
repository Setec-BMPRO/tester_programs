#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Arduino console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterFloat = console.ParameterFloat
ParameterBoolean = console.ParameterBoolean


class Arduino(console.BaseConsole):

    """Communications to SX-750 Arduino console."""

    # Auto add prompt to puts strings
    puts_prompt = '\r> '
    cmd_data = {
        'VERSION': ParameterString('VERSION?', read_format='{}'),
        'DEBUG': ParameterString('1 DEBUG', read_format='{}'),
        'QUIET': ParameterString('0 DEBUG', read_format='{}'),
        'PGM_5VSB': ParameterString('PROGRAM-5VSB', read_format='{}'),
        'PGM_PWRSW': ParameterString('PROGRAM-PWRSW', read_format='{}'),
        'OCP_MAX': ParameterString('OCP-MAX', read_format='{}'),
        '12_OCP_UNLOCK': ParameterString('12 OCP-UNLOCK', read_format='{}'),
        '24_OCP_UNLOCK': ParameterString('24 OCP-UNLOCK', read_format='{}'),
        'OCP_STEP_DN': ParameterString('OCP-STEP-DN', read_format='{}'),
        'OCP_LOCK': ParameterString('OCP-LOCK', read_format='{}'),
        }
