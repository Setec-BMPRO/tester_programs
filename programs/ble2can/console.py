#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLE2CAN Console driver."""

import share

# Some easier to use short names
Sensor = share.Sensor


class Console(share.SamB11Console):

    """Communications to BLE2CAN console."""

    cmd_data = {}
    override_commands = ()
