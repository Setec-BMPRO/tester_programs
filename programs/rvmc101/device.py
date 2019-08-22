#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101 Packet decoder."""

import ctypes
import logging
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

        @param packet RVCPacket instance

        """
        payload = packet.data
        if len(payload) != 8 or payload[0] != self.switch_status:
            raise PacketDecodeError()
        (   self.msgtype,
            switch_data,
            self.swver,
            self.counter,
            self.checksum,
            ) = struct.Struct('<BL3B').unpack(payload)
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


class NullPayload():

    """A NULL packet payload."""

    data = bytearray(8)


class CANReader(threading.Thread):

    """Thread to put CAN packets to the CANPacket device.

    This class is an asynchronous interface to the CAN packet stream sent
    by the RVMC101 product.
    Advertisment packets are received from the Serial2Can interface, decoded,
    and loaded into the tester.CANPacket logical device.
    That logical device is the data source for CAN based sensors.
    The RVMC101 transmits 25 packets/sec.

    """

    # Time to wait when not reading CAN packets
    wait_time = 0.1
    read_timeout = 1.0
    # A NULL Packet
    null_packet = Packet(NullPayload)

    def __init__(self, candev, packetdev, name=None):
        """Create instance

        @param candev CAN physical device (source of raw packets)
        @param packetdev RVMC101 CAN packet device

        """
        super().__init__(name=name)
        self.candev = candev
        self.packetdev = packetdev
        self.packetdev.packet = Packet(NullPayload)
        self._evt_stop = threading.Event()
        self._evt_enable = threading.Event()
        self.enable = False         # Default to be 'not enabled'
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Start CANReader')

    def run(self):
        """Run the data processing thread."""
        while not self._evt_stop.is_set():
            if self.enable:
                try:
                    pkt = self.candev.read_can(timeout=self.read_timeout)
                except tester.devphysical.can.SerialToCanError:
                    self._logger.debug('SerialToCanError')
                    self.packetdev.packet = self.null_packet
                    continue
                try:
                    self.packetdev.packet = Packet(pkt)
                except PacketDecodeError:
                    self._logger.debug('PacketDecodeError')
                    # Advertisment packets are mixed with the occasional other
                    # packet type, which will cause a decode error
                    pass
            else:
                self.candev.flush_can()
                time.sleep(self.wait_time)

    @property
    def enable(self):
        """Enable property getter.

        @return True if enabled

        """
        return self._evt_enable.is_set()

    @enable.setter
    def enable(self, value):
        """Set enable property.

        @param value True to enable packet processing

        """
        if value:
            self.packetdev.packet = self.null_packet
            self._evt_enable.set()
        else:
            self._evt_enable.clear()

    def halt(self):
        """Stop the packet processing thread."""
        self._logger.debug('Stop CANReader')
        self._evt_stop.set()
        self.join()

# TODO: This is how to send Display Control packets
#    def send_led_display(serial2can):
#        """Send a LED_DISPLAY packet."""
#        pkt = tester.devphysical.can.RVCPacket()
#        msg = pkt.header.message
#        msg.priority = 6
#        msg.reserved = 0
#        msg.DGN = tester.devphysical.can.RVCDGN.setec_led_display.value
#        msg.SA = tester.devphysical.can.RVCDeviceID.rvmn101.value
#        sequence = 1
#        # Show "88" on the display (for about 100msec)
#        # The 1st packet we send is ignored due to no previous sequence number
#        pkt.data.extend(b'\x01\xff\xff\xff\xff\xff')
#        pkt.data.extend(bytes([sequence & 0xff]))
#        pkt.data.extend(bytes([sum(pkt.data) & 0xff]))
#        serial2can.send('t{0}'.format(pkt))
#        sequence += 1
#        # The 2nd packet WILL be acted upon
#        pkt.data.clear()
#        pkt.data.extend(b'\x01\xFF\xFF\xFF\xFF\xFF')
#        pkt.data.extend(bytes([sequence & 0xff]))
#        pkt.data.extend(bytes([sum(pkt.data) & 0xff]))
#        serial2can.send('t{0}'.format(pkt))
#        sequence += 1
