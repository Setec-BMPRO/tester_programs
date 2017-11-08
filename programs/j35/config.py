#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Configuration."""


class J35():

    """Common configuration for all J35 versions."""

    sw_version = '1.3.15775.997'    # Software version


class J35A(J35):

    """J35A configuration."""

    hw_version = (2, 1, 'A')
    output_count = 7
    ocp_set = 20.0
    derate = True
    solar = False
    can = False


class J35B(J35):

    """J35B configuration."""

    hw_version = (2, 2, 'A')
    output_count = 14
    ocp_set = 35.0
    derate = False
    solar = False
    can = False


class J35C(J35):

    """J35C configuration."""

    hw_version = (7, 3, 'A')
    output_count = 14
    ocp_set = 35.0
    derate = False
    solar = True
    can = True
