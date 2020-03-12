#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 SETEC Pty Ltd
"""Trek2/JControl Configuration."""


class _Base():

    """Common configuration."""

    sw_version = '1.6.18204.326'
    sw_image = 'trek2_{0}.bin'.format(sw_version)


class Trek2(_Base):

    """Trek2 configuration."""

    hw_version = (7, 0, 'A')


class JControl(_Base):

    """JControl configuration."""

    hw_version = (4, 2, 'A')
