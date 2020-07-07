#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""C45A-15 Arduino console driver."""

import share


class Arduino(share.console.Base):

    """Communications to C45A-15 Arduino console."""

    cmd_data = {
        'VERSION': share.console.parameter.String(
            'VERSION?', read_format='{0}'),
        'DEBUG': share.console.parameter.String(
            '1 DEBUG', read_format='{0}'),
        'QUIET': share.console.parameter.String(
            '0 DEBUG', read_format='{0}'),
        'PGM_C45A15': share.console.parameter.String(
            'PROGRAM-C45A15', read_format='{0}'),
        }
