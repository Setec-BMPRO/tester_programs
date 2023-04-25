#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 SETEC Pty Ltd.
"""CAN Packet base classes."""

import abc

import attr


@attr.s
class DataDecoderMixIn(abc.ABC):  # pylint: disable=too-few-public-methods

    """ABC for all CAN packet data decoders."""

    fields = attr.ib(init=False, factory=dict)

    @abc.abstractmethod
    def decode(self, data):
        """Decode packet data."""


class DataDecodeError(Exception):

    """Error decoding a CAN packet."""
