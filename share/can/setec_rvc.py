#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""SETEC RV-C CAN Packet decoder & generator.

Reference:  "RVM101_5x CAN Specification"

"""

import ctypes
import enum
import struct

import attr
import tester


class DeviceID(enum.IntEnum):

    """RV-C CAN Device ID values for different SETEC products.

    Used for the packet Source Address (SA)

    """

    rvmc101 = 0x44
    rvmn101 = 0x54
    rvmd50 = rvmc101
    rvmn5x = rvmn101


class DGN(enum.IntEnum):

    """RV-C Data Group Number (DGN) values for message destinations."""

    proprietary_message = 0xEF00
    rvmc101 = proprietary_message + DeviceID.rvmc101.value
    rvmn101 = proprietary_message + DeviceID.rvmn101.value
    rvmd50 = proprietary_message + DeviceID.rvmd50.value
    rvmn5x = proprietary_message + DeviceID.rvmn5x.value


class SetecRVC(enum.IntEnum):

    """Generic SETEC RV-C CAN parameters."""

    data_len = 8            # Packets always have 8 bytes of data
    command_id_index = 0    # Command ID is 1st data byte
    message_id_index = 0    # Message ID is 1st data byte


@enum.unique
class CommandID(enum.IntEnum):

    """Command ID for packets sent from RVM[CD] to RVMN.

    5.5.10.1 RVMD50 Proprietary Message

    """

    switch_status = 0
    motor_control = 1
    output_control = 2
    dimming_control = 3
    special_command = 4
    object_control = 5
    read_request = 6
    write_parameter = 7
    pair_forget = 8
    device_info = 9
    device_status = 10


@enum.unique
class MessageID(enum.IntEnum):

    """Message ID for packets sent from RVMN to RVM[CD].

    5.5.10.2 RVMN5x Proprietary Message

    """

    _reserved = 0
    led_display = 1
    dimming_values = 2
    output_states = 3
    bridge_outputs_enabled = 4
    switch_inputs = 5
    system_status = 6
    analogue_inputs = 7
    output_error_states = 8
    serial_number = 9
    hvac_state = 10
    hvac_error = 11
    generator_type1_state = 12
    generator_type2_state = 13
    pairing_status = 14
    read_request = 15
    command = 16
    read_parameter = 17
    motor_config = 32
    tank_config = 33
    general_config = 34


class _SwitchStatusField(ctypes.Structure):

    """RVMC switch field definition.

    Refer to "RVM101 CAN Specification"

    """

    _fields_ = [
        ('_pairing', ctypes.c_uint, 2),
        ('retract', ctypes.c_uint, 2),
        ('extend', ctypes.c_uint, 2),
        ('_unused1', ctypes.c_uint, 2),
        ('zone1', ctypes.c_uint, 2),
        ('zone2', ctypes.c_uint, 2),
        ('zone3', ctypes.c_uint, 2),
        ('zone4', ctypes.c_uint, 2),
        ('_hex', ctypes.c_uint, 4),
        ('up', ctypes.c_uint, 2),
        ('down', ctypes.c_uint, 2),
        ('usb_pwr', ctypes.c_uint, 1),
        ('wake_up', ctypes.c_uint, 1),
        ('_unused2', ctypes.c_uint, 6),
        ]


class _SwitchStatusRaw(ctypes.Union):

    """Union of the RVMC switch type with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint),
        ('switch', _SwitchStatusField),
        ]


class SwitchStatusPacket():

    """A Switch Status packet."""

    def __init__(self, packet):
        """Create instance.

        @param packet CAN payload of SetecRVC.data_len bytes

        """
        payload = packet.data
        if (len(payload) != SetecRVC.data_len.value
                or payload[SetecRVC.command_id_index.value]
                    != CommandID.switch_status.value):
            raise tester.CANPacketDecodeError()
        (   self.msgtype,
            switch_data,
            self.swver,
            self.counter,
            self.checksum,
            ) = struct.Struct('<BL3B').unpack(payload)
        # Decode the switch data
        switch_raw = _SwitchStatusRaw()
        switch_raw.uint = switch_data
        zss = switch_raw.switch
        # Assign switch data to my properties
        self.retract = bool(zss.retract)
        self.extend = bool(zss.extend)
        self.zone1 = bool(zss.zone1)
        self.zone2 = bool(zss.zone2)
        self.zone3 = bool(zss.zone3)
        self.zone4 = bool(zss.zone4)
        self.up = bool(zss.up)
        self.down = bool(zss.down)
        self.usb_pwr = bool(zss.usb_pwr)
        self.wake_up = bool(zss.wake_up)


class _DeviceStatusField(ctypes.Structure):

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


class _DeviceStatusRaw(ctypes.Union):

    """Union of the button with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint, 16),
        ('button', _DeviceStatusField),
        ]


class DeviceStatusPacket():

    """A Device Status packet."""

    def __init__(self, packet):
        """Create instance.

        @param packet CAN payload of SetecRVC.data_len bytes

        """
        payload = packet.data
        if (len(payload) != SetecRVC.data_len.value
                or payload[SetecRVC.command_id_index.value]
                    not in (0, CommandID.device_status.value)):
            raise tester.CANPacketDecodeError()
        (   self.msgtype,       # D0
            button_data,        # D1,2
            self.menu_state,    # D3
            _,                  # D4-7
            ) = struct.Struct('<BHBL').unpack(payload)
        # Decode the button data
        button_raw = _DeviceStatusRaw()
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


class _RVMD50MessagePacket():

    """A RVMD50 message packet."""

    _cmd_id_index = 1           # Index of Cmd ID value
    _cmd_id_range = range(3)    # Valid range of Cmd ID values

    def __init__(self, serial2can, cmd_id):
        """Create instance.

        @param serial2can Serial2CAN device
        @param cmd_id Cmd ID value

        """
        self._serial2can = serial2can
        if cmd_id not in self._cmd_id_range:
            raise ValueError('Cmd ID out of range')
        self.pkt = tester.devphysical.can.RVCPacket()
        msg = self.pkt.header.message       # Packet...
        msg.DGN = DGN.rvmd50.value          #  to the RVMD50
        msg.SA = DeviceID.rvmn5x.value      #  from a RVMN5x
        self.pkt.data = bytearray(SetecRVC.data_len.value)
        self.pkt.data[SetecRVC.message_id_index.value] = (
            MessageID.command.value)
        self.pkt.data[self._cmd_id_index] = cmd_id

    def send(self):
        """Send the packet to the Serial2CAN device."""
        self._serial2can.send('t{0}'.format(self.pkt))


class RVMD50ControlLCDPacket(_RVMD50MessagePacket):

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


class RVMD50ResetPacket(_RVMD50MessagePacket):

    """A RVMD50 Reset packet."""

    _cmd_id = 1             # Cmd ID: 1 = Reset

    def __init__(self, serial2can):
        """Create instance.

        @param serial2can Serial2CAN device

        """
        super().__init__(serial2can, self._cmd_id)


class RVMD50ControlButtonPacket(_RVMD50MessagePacket):

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


@attr.s
class PacketPropertyReader():

    """Custom logical instrument to read CAN packet properties."""

    canreader = attr.ib()       # tester.CANReader instance
    packettype = attr.ib()      # CAN packet class
    _read_key = attr.ib(init=False, default=None)

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def opc(self):
        """Sensor: OPC."""
        self.canreader.opc()

    def read(self, callerid):
        """Sensor: Read payload data using the last configured key.

        @param callerid Identity of caller
        @return Packet property value

        """
        can_data = self.canreader.read(callerid)
        return getattr(self.packettype(can_data), self._read_key)
