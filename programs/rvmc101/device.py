#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101 Packet decoder."""

import ctypes
import struct
import threading
import time

import tester


class PacketDecodeError(Exception):

    """Error decoding RVMC101 status packet."""


class _SwitchField(ctypes.Structure):

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


class _SwitchRaw(ctypes.Union):

    """Union of the RVMC switch type with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint),
        ('switch', _SwitchField),
        ]


class Packet():

    """A RVMC101 broadcast packet."""

    switch_status = 0

    def __init__(self, packet):
        """Create instance.

        @param packet CANPacket instance

        """
        payload = packet.data
        if len(payload) != 8 or payload[0] != self.switch_status:
            raise PacketDecodeError()
        (   self.msgtype,
            switch_data,
            self.swver,
            self.counter,
            self.checksum,
            ) = struct.Struct('<BLB3').unpack(payload)
        # Decode the switch data
        switch_raw = _SwitchRaw()
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


class CANReader(threading.Thread):

    """Thread to put CAN packets to the CANPacket device.

    This class is an asynchronous interface to the CAN packet stream sent
    by the RVMC101 product.
    Advertisment packets are received from the Serial2Can interface, decoded,
    and loaded into the tester.CANPacket logical device.
    That logical device is the data source for CAN based sensors.

    """

    # Time to wait between reading CAN packets
    #  RVMC101 transmits 25 packets/sec.
    # We ignore most of them to reduce to processing load.
    wait_time = 0.2

    def __init__(self, candev, packetdev, name=None):
        """Create instance

        @param candev CAN physical device (source of raw packets)
        @param packetdev RVMC101 CAN packet device

        """
        super().__init__(name=name)
        self.candev = candev
        self.packetdev = packetdev
        self._stop = threading.Event()
        self._enable = threading.Event()
        self.enable = False         # Default to be 'not enabled'

    def run(self):
        """Run the data processing thread."""
        while not self._stop.is_set():
            if self.enable:
                self.candev.flush_can()
                try:
                    pkt = self.candev.read_can(timeout=0.1)
                except tester.devphysical.can.SerialToCanError:
                    self.packetdev.packet = None
                    continue
                try:
                    self.packetdev.packet = Packet(pkt)
                except PacketDecodeError:
                    # Advertisment packets are mixed with the occasional other
                    # packet type, which will cause a decode error
                    pass
            time.sleep(self.wait_time)

    @property
    def enable(self):
        """Enable property getter.

        @return True if enabled

        """
        return self._enable.is_set()

    @enable.setter
    def enable(self, value):
        """Set enable property.

        @param value True to enable packet processing

        """
        if value:
            self._enable.set()
        else:
            self._enable.clear()

    def stop(self):
        """Stop the packet processing thread."""
        self._stop.set()
        self.join()
