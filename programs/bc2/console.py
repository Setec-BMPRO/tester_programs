#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Console driver."""

import share


class Console(share.console.SamB11):

    """Communications to BC2 console."""

    cmd_data = {}
    override_commands = ()
