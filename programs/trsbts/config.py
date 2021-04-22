#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""TRS-BTx Configuration."""


class TrsBt2():

    """TRS-BT2 configuration."""

    sw_version = '2.0.20494.2194'       # PC-24735
    sw_image = 'trs-bts_factory_{0}.hex'.format(sw_version)
    hw_version = (3, 0, 'B')


class TrsBts():

    """TRS-BTS configuration."""

    sw_version = '2.0.20494.2194'       # PC-24906
    sw_image = 'trs-bts_factory_{0}.hex'.format(sw_version)
    hw_version = (3, 0, 'B')
