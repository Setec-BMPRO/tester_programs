#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""JControl/Trek2/Trek3 Configuration."""


class _Base():

    """Common configuration."""

    sw_version = '1.6.18204.326'
    sw_image = 'trek2_{0}.bin'.format(sw_version)


class JControl(_Base):

    """JControl configuration."""

    hw_version = (4, 2, 'A')


class Trek2(_Base):

    """Trek2 configuration."""

    hw_version = (7, 0, 'A')


class Trek3(_Base):

    """Trek3 configuration."""

    sw_version = '1.7.20320.327'
    sw_image = 'trek3_{0}.bin'.format(sw_version)
    hw_version = (1, 0, 'A')
