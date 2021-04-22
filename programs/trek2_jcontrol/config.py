#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""JControl/Trek2/Trek3 Configuration."""


class JControl():

    """JControl configuration."""

    sw_version = '1.7.20388.329'    # 035826 Rev 2      PC-24868
    sw_image = 'jcontrol_{0}.bin'.format(sw_version)
    hw_version = (4, 2, 'B')


class Trek2():

    """Trek2 configuration."""

    sw_version = '1.7.20512.331'    # 035862 Rev 2      MA-378
    sw_image = 'trek3_{0}.bin'.format(sw_version)
    hw_version = (7, 0, 'C')


class Trek3():

    """Trek3 configuration."""

    sw_version = '1.7.20512.331'    # 035862 Rev 2      PC-25163
    sw_image = 'trek3_{0}.bin'.format(sw_version)
    hw_version = (1, 0, 'B')
