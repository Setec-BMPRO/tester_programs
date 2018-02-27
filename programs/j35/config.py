#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Configuration."""


class J35():

    """Common configuration for all J35 versions."""

    sw_version = '1.4.17055.1365'   # Software version
    output_count = 14               # defaults for J35B,C
    ocp_set = 35.0
    solar = True


class J35A(J35):

    """J35A configuration."""

    hw_version = (9, 1, 'A')
    output_count = 7
    ocp_set = 20.0
    solar = False


class J35B(J35):

    """J35B configuration."""

    hw_version = (9, 2, 'A')


class J35C(J35):

    """J35C configuration."""

    hw_version = (9, 3, 'A')
