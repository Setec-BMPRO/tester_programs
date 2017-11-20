#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2/JControl Configuration."""

class _Trk2JCntl():

    """Common configuration."""

    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    hw_version = (6, 0, 'A')


class Trek2(_Trk2JCntl):

    """Trek2 configuration."""

    sw_version = '1.5.15833.150'
    product_name = 'Trek2'


class JControl(_Trk2JCntl):

    """JControl configuration."""

    sw_version = '1.6.16798.273'
    product_name = 'JControl'
