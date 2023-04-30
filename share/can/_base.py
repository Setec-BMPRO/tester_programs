#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 SETEC Pty Ltd.
"""CAN Packet base classes."""

import tester


# Protocol level definitions from the tester module
CANPacket = tester.devphysical.can.CANPacket
RVCHeader = tester.devphysical.can.RVCHeader
SETECHeader = tester.devphysical.can.SETECHeader
SETECMessageType = tester.devphysical.can.SETECMessageType
SETECDataID = tester.devphysical.can.SETECDataID
