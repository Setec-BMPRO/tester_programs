#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""ETrac-II Arduino console driver."""

import share


class Arduino(share.console.Arduino):

    """Communications to ETrac-II Arduino console."""

    cmd_data = {
        'VERSION': share.console.parameter.String(
            'VERSION?', read_format='{0}'),
        'DEBUG': share.console.parameter.String(
            '1 DEBUG', read_format='{0}'),
        'QUIET': share.console.parameter.String(
            '0 DEBUG', read_format='{0}'),
        'PGM_ETRAC2': share.console.parameter.String(
            'PROGRAM-ETRAC2', read_format='{0}'),
        }
