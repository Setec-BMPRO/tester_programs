#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""SETEC RV-C CAN Packet decoders & builders.

Reference:
    PLM/SYSTEMS/RVM5x/11_RD/60_Software/40_SW_Specifications/_Working/
        WIP_RVM101_5x CAN Specification_v0.6.docx

"""

import ctypes
import enum

import attr

from . import _base


class DeviceID(enum.IntEnum):

    """RV-C CAN Device ID values for different SETEC products.

    Used for the packet Source Address (SA)

    """

    RVMC101 = 0x44
    RVMN101 = 0x54
    RVMD50 = RVMC101
    RVMN5X = RVMN101


class DGN(enum.IntEnum):

    """RV-C Data Group Number (DGN) values for message destinations."""

    ACSTATUS1 = 0x1FFAD
    ACSTATUS3 = 0x1FFAB
    PROPRIETARY_MESSAGE = 0xEF00
    RVMC101 = PROPRIETARY_MESSAGE + DeviceID.RVMC101.value
    RVMN101 = PROPRIETARY_MESSAGE + DeviceID.RVMN101.value
    RVMD50 = PROPRIETARY_MESSAGE + DeviceID.RVMD50.value
    RVMN5X = PROPRIETARY_MESSAGE + DeviceID.RVMN5X.value


class SetecRVC(enum.IntEnum):

    """Generic SETEC RV-C CAN parameters."""

    DATA_LEN = 8  # Packets always have 8 bytes of data
    COMMAND_ID_INDEX = 0  # Command ID is 1st data byte
    MESSAGE_ID_INDEX = 0  # Message ID is 1st data byte


@enum.unique
class CommandID(enum.IntEnum):

    """Command ID for packets sent from RVM[CD] to RVMN.

    5.5.10.1 RVMD50 Proprietary Message

    """

    SWITCH_STATUS = 0
    MOTOR_CONTROL = 1
    OUTPUT_CONTROL = 2
    DIMMING_CONTROL = 3
    SPECIAL_COMMAND = 4
    OBJECT_CONTROL = 5
    READ_REQUEST = 6
    WRITE_PARAMETER = 7
    PAIR_FORGET = 8
    DEVICE_INFO = 9
    DEVICE_STATUS = 10


@enum.unique
class MessageID(enum.IntEnum):

    """Message ID for packets sent from RVMN to RVM[CD].

    5.5.10.2 RVMN5x Proprietary Message

    """

    _RESERVED = 0
    LED_DISPLAY = 1
    DIMMING_VALUES = 2
    OUTPUT_STATES = 3
    BRIDGE_OUTPUTS_ENABLED = 4
    SWITCH_INPUTS = 5
    SYSTEM_STATUS = 6
    ANALOGUE_INPUTS = 7
    OUTPUT_ERROR_STATES = 8
    SERIAL_NUMBER = 9
    HVAC_STATE = 10
    HVAC_ERROR = 11
    GENERATOR_TYPE1_STATE = 12
    GENERATOR_TYPE2_STATE = 13
    PAIRING_STATUS = 14
    READ_REQUEST = 15
    COMMAND = 16
    READ_PARAMETER = 17
    MOTOR_CONFIG = 32
    TANK_CONFIG = 33
    GENERAL_CONFIG = 34


class _SwitchStatus(ctypes.Structure):  # pylint: disable=too-few-public-methods

    """RVMC switch field definition.

    5.5.6 SWITCH_STATUS

    5.1 Data type definitions:
    "Bit fields" are 2-bit:
        11b – Data not available
        10b – Error
        01b – On
        00b – Off

    """

    _fields_ = [
        ("msgtype", ctypes.c_ulonglong, 8),  # D0
        ("pairing", ctypes.c_ulonglong, 2),  # D1-4...
        ("retract", ctypes.c_ulonglong, 2),
        ("extend", ctypes.c_ulonglong, 2),
        ("_unused1", ctypes.c_ulonglong, 2),  # Always 11b
        ("zone1", ctypes.c_ulonglong, 2),
        ("zone2", ctypes.c_ulonglong, 2),
        ("zone3", ctypes.c_ulonglong, 2),
        ("zone4", ctypes.c_ulonglong, 2),
        ("hex", ctypes.c_ulonglong, 4),  # Hex switch, 0000b if unused
        ("btnup", ctypes.c_ulonglong, 2),
        ("btndown", ctypes.c_ulonglong, 2),
        ("usb_pwr", ctypes.c_ulonglong, 1),
        ("wake_up", ctypes.c_ulonglong, 1),
        ("_unused2", ctypes.c_ulonglong, 6),  # Always 111111b
        ("swver", ctypes.c_ulonglong, 8),  # D5
        ("counter", ctypes.c_ulonglong, 8),  # D6
        ("checksum", ctypes.c_ulonglong, 8),  # D7
    ]


@attr.s
class SwitchStatusDecoder(_base.DataDecoderMixIn):

    """A RVMC Switch Status decoder."""

    def worker(self, packet, fields):
        """Decode packet.

        @param packet CANPacket instance
        @param fields Dictionary to hold decoded field data

        """
        data = packet.data
        if (
            len(data) != SetecRVC.DATA_LEN.value
            or data[SetecRVC.COMMAND_ID_INDEX.value] != CommandID.SWITCH_STATUS.value
        ):
            raise _base.DataDecodeError()
        zss = _SwitchStatus.from_buffer_copy(data)
        # pylint: disable=protected-access
        for name, _, bits in _SwitchStatus._fields_:
            value = getattr(zss, name)
            if bits < 3:
                value = bool(value) if value < 2 else None
            fields[name] = value


class _DeviceStatus(ctypes.Structure):  # pylint: disable=too-few-public-methods

    """RVMD50 button field definition.

    5.5.10.12 Command Signal and Parameter Definition

    """

    _fields_ = [
        ("msgtype", ctypes.c_ulonglong, 8),  # D0
        ("page", ctypes.c_ulonglong, 1),  # D1,2...
        ("sel", ctypes.c_ulonglong, 1),
        ("soft1", ctypes.c_ulonglong, 1),
        ("soft2", ctypes.c_ulonglong, 1),
        ("light1", ctypes.c_ulonglong, 1),
        ("light2", ctypes.c_ulonglong, 1),
        ("light3", ctypes.c_ulonglong, 1),
        ("pump", ctypes.c_ulonglong, 1),
        ("acmain", ctypes.c_ulonglong, 1),
        ("_reserved", ctypes.c_ulonglong, 6),  # Always 111111b
        ("backlight", ctypes.c_ulonglong, 1),
        ("menu_state", ctypes.c_ulonglong, 8),  # D3
        ("_unused", ctypes.c_ulonglong, 32),  # D4-7
    ]


@attr.s
class DeviceStatusDecoder(_base.DataDecoderMixIn):

    """RVMD50 Device Status decoder."""

    def worker(self, packet, fields):
        """Decode packet.

        @param packet CANPacket instance
        @param fields Dictionary to hold decoded field data

        """
        data = packet.data
        if (
            len(data) != SetecRVC.DATA_LEN.value
            or data[SetecRVC.COMMAND_ID_INDEX.value] != CommandID.DEVICE_STATUS.value
        ):
            raise _base.DataDecodeError()
        zss = _DeviceStatus.from_buffer_copy(data)
        # pylint: disable=protected-access
        for name, _, bits in _DeviceStatus._fields_:
            value = getattr(zss, name)
            if bits == 1:
                value = bool(value)
            fields[name] = value


class _ACStatus1(ctypes.Structure):  # pylint: disable=too-few-public-methods

    """Automatic Transfer Switch AC Status1 field definition.

    DGN = 0x1FFAD, Priority = 3,
    Rate = 50ms when L1+L2 current > 10A (Alternating Leg1/Leg2 packets)
    Current: uint16 from -1600A to 1612.5A, resolution 0.05A, offset 1600A
    Frequency: uint16 from 0Hz to 500Hz, resolution 1/128Hz

    """

    _fields_ = [
        ("instance", ctypes.c_ulonglong, 3),  # Always 001b
        ("iotype", ctypes.c_ulonglong, 1),
        ("source", ctypes.c_ulonglong, 3),  # Always 000b
        ("leg", ctypes.c_ulonglong, 1),
        ("voltage", ctypes.c_ulonglong, 16),  # Always 0xFFFF
        ("current", ctypes.c_ulonglong, 16),
        ("frequency", ctypes.c_ulonglong, 16),
        ("open_ground", ctypes.c_ulonglong, 2),
        ("open_neutral", ctypes.c_ulonglong, 2),
        ("polarity", ctypes.c_ulonglong, 2),
        ("groundcurrent", ctypes.c_ulonglong, 2),
    ]


class _ACStatus3(ctypes.Structure):  # pylint: disable=too-few-public-methods

    """Automatic Transfer Switch AC Status3 field definition.

    DGN = 0x1FFAB, Priority = 3,
    Rate = 1s (Alternating Leg1/Leg2 packets)

    """

    _fields_ = [
        ("instance", ctypes.c_ulonglong, 3),  # Always 001b
        ("iotype", ctypes.c_ulonglong, 1),
        ("source", ctypes.c_ulonglong, 3),  # Always 000b
        ("leg", ctypes.c_ulonglong, 1),
        ("waveform", ctypes.c_ulonglong, 2),  # Always 11b
        ("phase", ctypes.c_ulonglong, 4),
        ("_unused", ctypes.c_ulonglong, 2),  # Always 11b
        ("power_real", ctypes.c_ulonglong, 16),  # Always 0xFFFF
        ("power_reactive", ctypes.c_ulonglong, 16),  # Always 0xFFFF
        ("harmonics", ctypes.c_ulonglong, 8),  # Always 0xFF
        ("complementary_leg", ctypes.c_ulonglong, 8),  # Always 0xFF
    ]


@attr.s
class ACMONStatusDecoder(_base.DataDecoderMixIn):

    """ACMON Status decoder.

    ACMON units transmit 4 differnet packets, at 2 different rates:
    - ASStatus1_Leg1, ASStatus1_Leg2, ASStatus3_Leg1, ASStatus3_Leg2
    To get a complete dataset you need to see 1 of each of the 4 types.

    """

    ats1l1 = attr.ib(init=False, factory=dict)
    ats1l2 = attr.ib(init=False, factory=dict)
    ats3l1 = attr.ib(init=False, factory=dict)
    ats3l2 = attr.ib(init=False, factory=dict)

    def worker(self, packet, fields):
        """Decode packet.

        @param packet CANPacket instance
        @param fields Dictionary to hold decoded field data

        """
        data = packet.data
        dgn = packet.header.message.DGN
        if len(data) != SetecRVC.DATA_LEN.value:
            raise _base.DataDecodeError()
        field_groups = [  # (Dictionary, Prefix)
            (self.ats1l1, "S1L1", ),
            (self.ats1l2, "S1L2", ),
            (self.ats3l1, "S3L1", ),
            (self.ats3l2, "S3L2", ),
            ]
        # pylint: disable=protected-access
        if dgn == DGN.ACSTATUS1:
            ats_fields = _ACStatus1.from_buffer_copy(data)
            ats_names = _ACStatus1._fields_
            index = 0
        elif dgn == DGN.ACSTATUS3:
            ats_fields = _ACStatus3.from_buffer_copy(data)
            ats_names = _ACStatus3._fields_
            index = 2
        else:
            raise _base.DataDecodeError()
        index += getattr(ats_fields, "leg")  # 0-3
        group, _ = field_groups[index]  # Choose 1 of 4 field dictionaries
        group.clear()
        for name, _, _ in ats_names:
            group[name] = getattr(ats_fields, name)
        # Merge the 4 field dictionaries into fields
        for group, prefix in field_groups:
            for key, value in group.items():
                fields["{0}_{1}".format(prefix, key)] = value


@attr.s
class RVMC101ControlLEDBuilder:  # pylint: disable=too-few-public-methods

    """A RVMC101 Control LED packet builder.

    [0]: LED Display = 0x01
    [1]: LED 7 segment DIGIT0 (LSB, right)
    [2]: LED 7 segment DIGIT1 (MSB, left)
    [3.0]: 1 = Enable power to USB (Default)
    [3.1]: 1 = Stay Awake
    [3.2-7]: Unused: 0xFC
    [4-5]: Unused: 0xFF
    [6]: Sequence number
    [7]: Checksum

    """

    packet = attr.ib(init=False)

    @packet.default
    def _packet_default(self):
        """Populate CAN Packet."""
        header = _base.RVCHeader()
        msg = header.message
        msg.DGN = DGN.RVMC101.value  #  to the RVMC101
        msg.SA = DeviceID.RVMN101.value  #  from a RVMN101
        data = bytearray([MessageID.LED_DISPLAY.value])
        data.extend(b"\x00\x00\xff\xff\xff\x00\x00")
        return _base.CANPacket(header, data)

    @property
    def pattern(self):
        """pattern property getter.

        @return Test pattern value

        """
        return self.packet.data[1]

    @pattern.setter
    def pattern(self, value):
        """Set pattern property.

        @param value Test pattern

        """
        self.packet.data[1] = self.packet.data[2] = value
        self.packet.data[6] = (self.packet.data[6] + 1) & 0xFF  # Sequence number
        self.packet.data[7] = sum(self.packet.data[:7]) & 0xFF  # Checksum


class _RVMD50Message:  # pylint: disable=too-few-public-methods

    """A generic RVMD50 message packet."""

    _cmd_id_index = 1  # Index of Cmd ID value
    _cmd_id_range = range(3)  # Valid range of Cmd ID values

    @classmethod
    def create(cls, cmd_id):
        """Create instance.

        @param cmd_id Cmd ID value
        @return CANPacket instance

        """
        if cmd_id not in cls._cmd_id_range:
            raise ValueError("Cmd ID out of range")
        header = _base.RVCHeader()
        msg = header.message  # Packet...
        msg.DGN = DGN.RVMD50.value  #  to the RVMD50
        msg.SA = DeviceID.RVMN5X.value  #  from a RVMN5x
        data = bytearray(SetecRVC.DATA_LEN.value)
        data[SetecRVC.MESSAGE_ID_INDEX.value] = MessageID.COMMAND.value
        data[cls._cmd_id_index] = cmd_id
        return _base.CANPacket(header, data)


@attr.s
class RVMD50ControlLCDBuilder:  # pylint: disable=too-few-public-methods

    """A RVMD50 Control LCD packet builder."""

    _pattern_index = 2  # Index of test pattern value

    # Cmd ID: 0 = Control LCD
    packet = attr.ib(init=False, factory=lambda: _RVMD50Message.create(cmd_id=0))

    def __attrs_post_init__(self):
        """Populate fields."""
        self.pattern = 0

    @property
    def pattern(self):
        """pattern property getter.

        @return Test pattern value (0-3)

        """
        return self.packet.data[self._pattern_index]

    @pattern.setter
    def pattern(self, value):
        """Set pattern property.

        @param value Test pattern (0-3)

        """
        if value not in range(4):
            raise ValueError("Test pattern must be 0-3")
        self.packet.data[self._pattern_index] = value


@attr.s
class RVMD50ResetBuilder:  # pylint: disable=too-few-public-methods

    """A RVMD50 Reset packet builder."""

    # Cmd ID: 1 = Reset
    packet = attr.ib(init=False, factory=lambda: _RVMD50Message.create(cmd_id=1))


@attr.s
class RVMD50ControlButtonBuilder:

    """A RVMD50 Control Button packet builder."""

    _group_id_index = 2  # Index of Group ID value
    _button_index = 3  # Index of Button value

    # Cmd ID: 2 = Control Button
    packet = attr.ib(init=False, factory=lambda: _RVMD50Message.create(cmd_id=2))

    def __attrs_post_init__(self):
        """Populate fields."""
        self.enable = False
        self.button = False

    @property
    def enable(self):
        """Enable property getter.

        @return Test button value (0-3)

        """
        return bool(self.packet.data[self._group_id_index])

    @enable.setter
    def enable(self, value):
        """Set enable property.

        @param value Enable True/False

        """
        if not isinstance(value, bool):
            raise ValueError("Enable must be boolean")
        self.packet.data[self._group_id_index] = int(value)

    @property
    def button(self):
        """button property getter.

        @return Button value boolean

        """
        return bool(self.packet.data[self._button_index])

    @button.setter
    def button(self, value):
        """Set button property. Pushes the 'Page' button: 0x01.

        @param value Button True/False

        """
        if not isinstance(value, bool):
            raise ValueError("Button must be boolean")
        self.packet.data[self._button_index] = int(value)
