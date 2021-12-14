#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""RvView/JDisplay Configuration."""


class JDisplay():

    """JDisplay configuration."""

    sw_version = '1.0.17318.27'
    sw_file = 'JDisplay_{0}.bin'.format(sw_version)
    hw_version = (3, 0, 'A')


class RvView():

    """RvView configuration."""

    sw_version = '1.1.16188.1004'
    sw_file = 'RvView_{0}.bin'.format(sw_version)
    hw_version = (3, 0, 'A')


class RvView2():

    """RvView2 NXP micro configuration."""

    sw_version = '1.2.20314.1010'
    sw_file = 'RvView2_{0}.bin'.format(sw_version)
    hw_version = (1, 0, 'A')


class RvView2a():

    """RvView2 ATSAMC21 micro configuration."""

    sw_file = 'RvView2a_1.4.0-0-gae44ae2.bin'
