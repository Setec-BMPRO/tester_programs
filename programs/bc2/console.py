#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Console driver."""

import share

# Some easier to use short names
Sensor = share.Sensor


class Console(share.SamB11Console):

    """Communications to BC2 console."""

    cmd_data = {}
    override_commands = ()
