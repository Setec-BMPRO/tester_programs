#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A Tunneled Console over CAN.

Creates an interface to tunnel data across a CAN bus to a remote device
console. Our end of the tunnel is a Trek2 PCB, which we talk to using the
console serial port.
The interface is compatible with that of a SimSerial port.
This driver implements a very simplified version of the generic console
driver. Just enough to open and run a tunnel.
"""

# "CAN Print Packets" mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF

"""
The required command etc to run a tunnel...

Echo OFF
    '0 ECHO'                    ' -> \r\n> '
CAN Filter
    '"RF,ALL CAN'               None
CAN Print Packets
    '"STATUS XN?'               '0x12345678'
    '0x12345678 "STATUS XN!'    None
Open CAN Tunnel
    '"TCC,{},3,{},1 CAN'        None

Send Data
    '"TCC,{},4,{} CAN'          None
Receive Data
    None                        'RRC,{},4,{count},{data},...'

Close CAN Tunnel
    '"TCC,{},3,{},0 CAN'        None
"""
