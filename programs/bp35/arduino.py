#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""BP35 / BP35-II Initial Test Programs."""

import share


class Arduino(share.console.Arduino):

    """Communications to BP35 / BP35-II Arduino programmer console."""

    cmd_data = {
        'VERSION': share.console.parameter.String(
            'VERSION?', read_format='{0}'),
        'DEBUG': share.console.parameter.String(
            '1 DEBUG', read_format='{0}'),
        'QUIET': share.console.parameter.String(
            '0 DEBUG', read_format='{0}'),
        'PGM_BP35SR': share.console.parameter.String(
            'PROGRAM-BP35SR', read_format='{0}'),
        }
