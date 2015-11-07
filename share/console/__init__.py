#!/usr/bin/env python3
"""Serial Console Drivers."""


class CmdRespError(Exception):
    """Command response error."""


__all__ = ['arm_gen0', 'arm_gen1']


# Easy access to utility methods and classes
from ._base import *
from .arm_gen0 import *
from .arm_gen1 import *
