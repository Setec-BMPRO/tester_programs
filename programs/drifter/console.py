#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter console driver."""

import share


class Console(share.console.Base):

    """Communications to Drifter console."""

    parameter = share.console.parameter
    cmd_data = {
        'UNLOCK': parameter.Boolean(
            'XDEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': parameter.Boolean(
            'NV-WRITE-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'NVSTATUS': parameter.Float('NV-STATUS PRINT', read_format='{0}'),
        'RESTART': parameter.Boolean(
            'RESTART', writeable=True, readable=False, write_format='{1}',
            write_expected=3),
        'APS_DISABLE': parameter.Float(
            'APS-DISABLE',
            writeable=True, readable=False, write_format='{0} {1}'),
        'CAL_RELOAD': parameter.Boolean(
            'CAL-RELOAD', writeable=True, readable=False, write_format='{1}'),
        'CAL_I_ZERO': parameter.Boolean(
            'CAL-I-ZERO', writeable=True, readable=False, write_format='{1}'),
        'CAL_I_SLOPE': parameter.Float(
            'CAL-I-SLOPE',
            writeable=True, readable=False, scale=1000,
            minimum=-200000, maximum=200000, write_format='{0} {1}'),
        'CAL_V_SLOPE': parameter.Float(
            'CAL-V-SLOPE',
            writeable=True, readable=False, scale=1000,
            write_format='{0} {1}'),
        'CAL_OFFSET_CURRENT': parameter.Float(
            'X-CAL-OFFSET-CURRENT',
            writeable=True, scale=1, minimum=-1000,
            write_format='{0} {1} X!', read_format='{0} X?'),
        'VOLTAGE': parameter.Float(
            'X-VOLTS-FILTERED', scale=1000, read_format='{0} X?'),
        'CURRENT': parameter.Float(
            'X-CURRENT-FILTERED', scale=1000, read_format='{0} X?'),
        'ZERO_CURRENT': parameter.Float(
            'X-CURRENT-FILTERED', scale=1, read_format='{0} X?'),
        'ZERO-CURRENT-DISPLAY-THRESHOLD': parameter.Float(
            'X-ZERO-CURRENT-DISPLAY-THRESHOLD',
            writeable=True, scale=1, minimum=-1000,
            write_format='{0} {1} X!', read_format='{0} X?'),
        'V_FACTOR': parameter.Float(
            'X-CAL-FACTOR-VOLTS', read_format='{0} X?'),
        'I_FACTOR': parameter.Float(
            'X-CAL-FACTOR-CURRENT', read_format='{0} X?'),
        }
    # Strings to ignore in responses
    ignore = (' ', )
