#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 SETEC Pty Ltd.
"""SETEC RV-C CAN Packet decoder & generator.

Reference:  "RVM101_5x CAN Specification"

"""

import contextlib
import ctypes
import enum
import struct

import attr
import tester


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


class PacketDecodeError(Exception):

    """Error decoding a CAN packet."""


class _SwitchStatusField(ctypes.Structure):

    """RVMC switch field definition.

    Refer to "RVM101 CAN Specification"

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("_pairing", ctypes.c_uint, 2),
        ("retract", ctypes.c_uint, 2),
        ("extend", ctypes.c_uint, 2),
        ("_unused1", ctypes.c_uint, 2),
        ("zone1", ctypes.c_uint, 2),
        ("zone2", ctypes.c_uint, 2),
        ("zone3", ctypes.c_uint, 2),
        ("zone4", ctypes.c_uint, 2),
        ("_hex", ctypes.c_uint, 4),
        ("btnup", ctypes.c_uint, 2),
        ("btndown", ctypes.c_uint, 2),
        ("usb_pwr", ctypes.c_uint, 1),
        ("wake_up", ctypes.c_uint, 1),
        ("_unused2", ctypes.c_uint, 6),
    ]


class _SwitchStatusRaw(ctypes.Union):

    """Union of the RVMC switch type with unsigned integer."""

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("uint", ctypes.c_uint),
        ("switch", _SwitchStatusField),
    ]


@attr.s
class SwitchStatusPacket:  # pylint: disable=too-few-public-methods

    """A RVMC Switch Status packet."""

    data = attr.ib(validator=attr.validators.instance_of(bytes))
    fields = attr.ib(init=False, factory=dict)

    def __attrs_post_init__(self):
        """Populate fields."""
        if (
            len(self.data) != SetecRVC.DATA_LEN.value
            or self.data[SetecRVC.COMMAND_ID_INDEX.value]
            != CommandID.SWITCH_STATUS.value
        ):
            raise PacketDecodeError()
        (
            self.fields["msgtype"],  # D0
            switch_data,  # D1-4
            self.fields["swver"],  # D5
            self.fields["counter"],  # D6
            self.fields["checksum"],  # D7
        ) = struct.Struct("<BL3B").unpack(self.data)
        # Decode the switch data
        switch_raw = _SwitchStatusRaw()
        # pylint: disable=attribute-defined-outside-init
        switch_raw.uint = switch_data
        zss = switch_raw.switch
        # pylint: disable=protected-access
        for name in tuple(field[0] for field in _SwitchStatusField._fields_):
            self.fields[name] = getattr(zss, name)


class _DeviceStatusField(ctypes.Structure):

    """RVMD50 button field definition.

    Refer to "RVMN101_5x CAN Specification"

    """

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("page", ctypes.c_uint, 1),
        ("sel", ctypes.c_uint, 1),
        ("soft1", ctypes.c_uint, 1),
        ("soft2", ctypes.c_uint, 1),
        ("light1", ctypes.c_uint, 1),
        ("light2", ctypes.c_uint, 1),
        ("light3", ctypes.c_uint, 1),
        ("pump", ctypes.c_uint, 1),
        ("acmain", ctypes.c_uint, 1),
        ("_reserved", ctypes.c_uint, 6),
        ("backlight", ctypes.c_uint, 1),
    ]


class _DeviceStatusRaw(ctypes.Union):

    """Union of the button with unsigned integer."""

    # pylint: disable=too-few-public-methods
    _fields_ = [
        ("uint", ctypes.c_uint, 16),
        ("button", _DeviceStatusField),
    ]


@attr.s
class DeviceStatusPacket:  # pylint: disable=too-few-public-methods

    """RVMD50 Device Status packet."""

    data = attr.ib(validator=attr.validators.instance_of(bytes))
    fields = attr.ib(init=False, factory=dict)

    def __attrs_post_init__(self):
        """Populate fields."""
        if (
            len(self.data) != SetecRVC.DATA_LEN.value
            or self.data[SetecRVC.COMMAND_ID_INDEX.value]
            != CommandID.DEVICE_STATUS.value
        ):
            raise PacketDecodeError()
        (
            self.fields["msgtype"],  # D0
            button_data,  # D1,2
            self.fields["menu_state"],  # D3
            self.fields["_unused"],  # D4-7
        ) = struct.Struct("<BHBL").unpack(self.data)
        # Decode the button data
        button_raw = _DeviceStatusRaw()
        # pylint: disable=attribute-defined-outside-init
        button_raw.uint = button_data
        zss = button_raw.button
        # pylint: disable=protected-access
        for name in tuple(field[0] for field in _DeviceStatusField._fields_):
            self.fields[name] = getattr(zss, name)


class _RVMD50MessagePacket:  # pylint: disable=too-few-public-methods

    """A RVMD50 message packet."""

    _cmd_id_index = 1  # Index of Cmd ID value
    _cmd_id_range = range(3)  # Valid range of Cmd ID values

    def __init__(self, candev, cmd_id):
        """Create instance.

        @param candev CAN device
        @param cmd_id Cmd ID value

        """
        self._candev = candev
        if cmd_id not in self._cmd_id_range:
            raise ValueError("Cmd ID out of range")
        header = tester.devphysical.can.RVCHeader()
        msg = header.message  # Packet...
        msg.DGN = DGN.RVMD50.value  #  to the RVMD50
        msg.SA = DeviceID.RVMN5X.value  #  from a RVMN5x
        data = bytearray(SetecRVC.DATA_LEN.value)
        data[SetecRVC.MESSAGE_ID_INDEX.value] = MessageID.COMMAND.value
        data[self._cmd_id_index] = cmd_id
        self.pkt = tester.devphysical.can.CANPacket(header, data)

    def send(self):
        """Send the packet to the CAN bus."""
        self._candev.send(self.pkt)


class RVMD50ControlLCDPacket(_RVMD50MessagePacket):

    """A RVMD50 Control LCD packet."""

    _cmd_id = 0  # Cmd ID: 0 = Control LCD
    _pattern_index = 2  # Index of test pattern value

    def __init__(self, candev):
        """Create instance.

        @param candev 2CAN device

        """
        super().__init__(candev, self._cmd_id)
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
            raise ValueError("Test pattern must be 0-3")
        self.pkt.data[self._pattern_index] = value


class RVMD50ResetPacket(_RVMD50MessagePacket):

    """A RVMD50 Reset packet."""

    # pylint: disable=too-few-public-methods
    _cmd_id = 1  # Cmd ID: 1 = Reset

    def __init__(self, candev):
        """Create instance.

        @param candev CAN device

        """
        super().__init__(candev, self._cmd_id)


class RVMD50ControlButtonPacket(_RVMD50MessagePacket):

    """A RVMD50 Control Button packet."""

    _cmd_id = 2  # Cmd ID: 2 = Control Button
    _group_id = 1  # Group ID: 0 = Off, 1 = On
    _group_id_index = 2  # Index of Group ID value
    _button_index = 3  # Index of button value

    def __init__(self, candev):
        """Create instance.

        @param candev CAN device

        """
        super().__init__(candev, self._cmd_id)
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
            raise ValueError("Enable must be boolean")
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
            raise ValueError("Button must be boolean")
        self.pkt.data[self._button_index] = int(value)


class ACMONStatusPacket:  # pylint: disable=too-few-public-methods

    """ACMON Status packet."""


# TODO: Implement ACMON CAN Packet decoder


@attr.s
class PacketPropertyReader:

    """Custom logical instrument to read CAN packet properties."""

    canreader = attr.ib()  # tester.CANReader instance
    packettype = attr.ib()  # CAN packet class
    _read_key = attr.ib(init=False, default=None)

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def opc(self):
        """Sensor: OPC."""

    def read(self, callerid):  # pylint: disable=unused-argument
        """Sensor: Read payload data using the last configured key.

        @param callerid Identity of caller
        @return Packet property value

        """
        try:
            pkt = self.canreader.read()
            packet = self.packettype(pkt.data)
        except tester.CANReaderError:  # A timeout due to no traffic
            return None
        except PacketDecodeError:  # Probably incorrect packet type
            return None
        return packet.fields[self._read_key]


@attr.s
class PacketDetector:

    """Custom logical instrument to detect CAN packet traffic."""

    canreader = attr.ib()  # tester.CANReader instance

    def configure(self, key):  # pylint: disable=unused-argument
        """Sensor: Configure for next reading."""

    def opc(self):
        """Sensor: OPC."""

    def read(self, callerid):  # pylint: disable=unused-argument
        """Sensor: Read presence of CAN traffic.

        @param callerid Identity of caller
        @return True if CAN traffic is seen

        """
        result = None
        with contextlib.suppress(tester.CANReaderError):
            self.canreader.read()
            result = True
        return result
