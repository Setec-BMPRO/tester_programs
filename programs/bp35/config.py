#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Configuration."""


class BP35():

    """Common configuration for all versions."""

    arm_sw_version = '2.0.17344.4603'
    pic_sw_version = '1.5.16253.282'
    pic_hw_version = 4


class BP35SR(BP35):

    """BP35SR configuration."""

    arm_hw_version = (12, 1, 'B')

class BP35PM(BP35):

    """BP35PM configuration."""

    arm_hw_version = (12, 2, 'B')


class BP35HA(BP35):

    """BP35HA configuration."""

    arm_hw_version = (12, 3, 'B')
