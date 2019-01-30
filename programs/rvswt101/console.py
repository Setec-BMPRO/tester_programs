#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVSWT101 Console driver."""

import share

class Console(share.console.BadUart):

    """Communications to RVSWT101 console."""

    parameter = share.console.parameter
    cmd_data = {
        'SW_VER': parameter.String('SW-VERSION', read_format='{0}?'),
        }
