#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVMC101 console driver."""

import share


class _Console():

    """Base class for a RVMC101 console."""

    # "CAN Bound" is STATUS bit 28
    _can_bound = (1 << 28)
    parameter = share.console.parameter
    cmd_data = {
        'SW_VER': parameter.String('SW-VERSION', read_format='{0}?'),
        'CAN_BIND': parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=_can_bound),
        'CAN': parameter.String(
            'CAN', writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': parameter.Hex('CANSTATS', read_format='{0}?'),
        }


class TunnelConsole(_Console, share.console.CANTunnel):

    """Console for a CAN tunneled connection to a RVMC101."""
