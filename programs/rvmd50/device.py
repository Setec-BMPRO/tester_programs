#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""RVMD50 Packet decoder."""

import ctypes
import struct

import tester


class _RVMD50ButtonField(ctypes.Structure):

    """RVMD50 button field definition.

    Refer to "RVMN101_5x CAN Specification"

    """

    _fields_ = [
        # Byte D1
        ('page', ctypes.c_uint, 1),
        ('sel', ctypes.c_uint, 1),
        ('soft1', ctypes.c_uint, 1),
        ('soft2', ctypes.c_uint, 1),
        ('light1', ctypes.c_uint, 1),
        ('light2', ctypes.c_uint, 1),
        ('light3', ctypes.c_uint, 1),
        ('pump', ctypes.c_uint, 1),
        # Byte D2
        ('acmain', ctypes.c_uint, 1),
        ('_reserved', ctypes.c_uint, 6),
        ('backlight', ctypes.c_uint, 1),
        ]


class _RVMD50ButtonRaw(ctypes.Union):

    """Union of the button with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint, 16),
        ('button', _RVMD50ButtonField),
        ]


class RVMD50StatusPacket():

    """A RVMD50 device status packet."""

    device_status_id = 10

    def __init__(self, packet):
        """Create instance.

        @param packet CAN payload of 8 bytes

        """
        payload = packet.data
        if len(payload) != 8 or payload[0] not in (0, self.device_status_id):
            raise tester.CANPacketDecodeError()
        (   self.msgtype,       # D0
            button_data,        # D1,2
            self.menu_state,    # D3
            _,                  # D4-7
            ) = struct.Struct('<BHBL').unpack(payload)
        # Decode the button data
        button_raw = _RVMD50ButtonRaw()
        button_raw.uint = button_data
        zss = button_raw.button
        # Assign button data to my properties
        self.page = bool(zss.page)
        self.sel = bool(zss.sel)
        self.soft1 = bool(zss.soft1)
        self.soft2 = bool(zss.soft2)
        self.light1 = bool(zss.light1)
        self.light2 = bool(zss.light2)
        self.light3 = bool(zss.light3)
        self.pump = bool(zss.pump)
        self.acmain = bool(zss.acmain)
        self.backlight = bool(zss.backlight)


class RVMD50CommandPacket():

    """A RVMD50 command packet."""

    _status_id = 16         # Status ID: 16 = Command
    _status_id_index = 0    # Index of Status ID value
    _cmd_id_index = 1       # Index of Cmd ID value

    def __init__(self, serial2can, cmd_id):
        """Create instance.

        @param serial2can Serial2CAN device
        @param cmd_id Cmd ID value

        """
        self._serial2can = serial2can
        if cmd_id not in range(3):
            raise ValueError('Cmd ID must be 0-2')
        self.pkt = tester.devphysical.can.RVCPacket()
        msg = self.pkt.header.message
        msg.priority = 6
        msg.reserved = 0
        msg.DGN = tester.devphysical.can.RVCDGN.setec_rvmd50.value
        msg.SA = tester.devphysical.can.RVCDeviceID.rvmn5x.value
        self.pkt.data = bytearray(8)
        self.pkt.data[self._status_id_index] = self._status_id
        self.pkt.data[self._cmd_id_index] = cmd_id

    def send(self):
        """Send the packet to the Serial2CAN device."""
        self._serial2can.send('t{0}'.format(self.pkt))


class RVMD50ControlLCDPacket(RVMD50CommandPacket):

    """A RVMD50 Control LCD packet."""

    _cmd_id = 0             # Cmd ID: 0 = Control LCD
    _pattern_index = 2      # Index of test pattern value

    def __init__(self, serial2can):
        """Create instance.

        @param serial2can Serial2CAN device

        """
        super().__init__(serial2can, self._cmd_id)
        self.pattern = 0

    @property
    def pattern(self):
        """pattern property getter.

        @return Test pattern value (0-3)

        """
        return self.pkt.data[self._pattern_index]

    @pattern.setter
    def pattern(self, value):
        """Set pattern property.

        @param value Test pattern (0-3)

        """
        if value not in range(4):
            raise ValueError('Test pattern must be 0-3')
        self.pkt.data[self._pattern_index] = value


class RVMD50ResetPacket(RVMD50CommandPacket):

    """A RVMD50 Reset packet."""

    _cmd_id = 1             # Cmd ID: 1 = Reset

    def __init__(self, serial2can):
        """Create instance.

        @param serial2can Serial2CAN device

        """
        super().__init__(serial2can, self._cmd_id)


class RVMD50ControlButtonPacket(RVMD50CommandPacket):

    """A RVMD50 Control Button packet."""

    _cmd_id = 2             # Cmd ID: 2 = Control Button
    _group_id = 1           # Group ID: 0 = Off, 1 = On
    _group_id_index = 2     # Index of Group ID value
    _button_index = 3       # Index of button value

    def __init__(self, serial2can):
        """Create instance.

        @param serial2can Serial2CAN device

        """
        super().__init__(serial2can, self._cmd_id)
        self.enable = False
        self.button = False

    @property
    def enable(self):
        """Enable property getter.

        @return Test button value (0-3)

        """
        return bool(self.pkt.data[self._group_id_index])

    @enable.setter
    def enable(self, value):
        """Set enable property.

        @param value Enable True/False

        """
        if not isinstance(value, bool):
            raise ValueError('Enable must be boolean')
        self.pkt.data[self._group_id_index] = int(value)

    @property
    def button(self):
        """button property getter.

        @return Button value boolean

        """
        return bool(self.pkt.data[self._button_index])

    @button.setter
    def button(self, value):
        """Set button property. Pushes the 'Page' button: 0x01.

        @param value Button True/False

        """
        if not isinstance(value, bool):
            raise ValueError('Button must be boolean')
        self.pkt.data[self._button_index] = int(value)
