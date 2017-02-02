#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Test Program."""

import tester
import share
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        # Power USB devices + Fixture Trek2.
        self.dcs_Vcom = tester.DCSource(devices['DCS1'])
        # Power unit under test.
        self.dcs_Vin = tester.DCSource(devices['DCS2'])
        # As the water level rises the "switches" close. The order of switch
        # closure does not matter, just the number closed.
        # The lowest bar always flashes. Closing these relays makes the other
        # bars come on.
        self.rla_s1 = tester.Relay(devices['RLA3'])
        self.rla_s2 = tester.Relay(devices['RLA4'])
        self.rla_s3 = tester.Relay(devices['RLA5'])
        # Connection to the Serial-to-CAN Trek2 inside the fixture
        ser_can = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        ser_can.port = limit.CAN_PORT
        # CAN Console tunnel driver
        self.tunnel = share.ConsoleCanTunnel(
            port=ser_can, simulation=fifo, verbose=False)
        # Trek2 Console driver (using the CAN Tunnel)
        self.trek2 = console.TunnelConsole(port=self.tunnel, verbose=False)

    def reset(self):
        """Reset instruments."""
        try:
            self.trek2.close()
        except Exception:   # Ignore serial port close errors
            pass
        self.dcs_Vin.output(0.0, output=False)
        self.dcs_Vcom.output(0.0, output=False)
        for rla in (self.rla_s1, self.rla_s2, self.rla_s3):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        trek2 = logical_devices.trek2
        sensor = tester.sensor
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.oYesNoSeg = sensor.YesNo(
            message=tester.translate('trek2_final', 'AreSegmentsOn?'),
            caption=tester.translate('trek2_final', 'capSegments'))
        self.oYesNoBklight = sensor.YesNo(
            message=tester.translate('trek2_final', 'IsBacklightOk?'),
            caption=tester.translate('trek2_final', 'capBacklight'))
        tank1 = console.Sensor(trek2, 'TANK1')
        tank2 = console.Sensor(trek2, 'TANK2')
        tank3 = console.Sensor(trek2, 'TANK3')
        tank4 = console.Sensor(trek2, 'TANK4')
        self.otanks = (tank1, tank2, tank3, tank4)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement

        self.ui_YesNoSeg = Measurement(
            limits['Notify'], sense.oYesNoSeg)
        self.ui_YesNoBklight = Measurement(
            limits['Notify'], sense.oYesNoBklight)
        self.arm_level1 = []
        self.arm_level2 = []
        self.arm_level3 = []
        self.arm_level4 = []
        for sens in sense.otanks:
            self.arm_level1.append(Measurement(limits['ARM-level1'], sens))
            self.arm_level2.append(Measurement(limits['ARM-level2'], sens))
            self.arm_level3.append(Measurement(limits['ARM-level3'], sens))
            self.arm_level4.append(Measurement(limits['ARM-level4'], sens))
