#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Test Program."""

import tester
import sensor
import share
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
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

    def trek2_puts(self,
                   string_data, preflush=0, postflush=0, priority=False,
                   addprompt=True):
        """Push string data into the buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.trek2.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.trek2.close()
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
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.oYesNoSeg = sensor.YesNo(
            message=tester.translate('trek2_final', 'AreSegmentsOn?'),
            caption=tester.translate('trek2_final', 'capSegments'))
        self.oYesNoBklight = sensor.YesNo(
            message=tester.translate('trek2_final', 'IsBacklightOk?'),
            caption=tester.translate('trek2_final', 'capBacklight'))
        self.oYesNoDisplay = sensor.YesNo(
            message=tester.translate('trek2_final', 'IsDisplayOk?'),
            caption=tester.translate('trek2_final', 'capDisplay'))
        self.oYesNoLevel = sensor.YesNo(
            message=tester.translate('trek2_final', 'IsLevelOk?'),
            caption=tester.translate('trek2_final', 'capLevel'))
        self.tank1 = console.Sensor(trek2, 'TANK1')
        self.tank2 = console.Sensor(trek2, 'TANK2')
        self.tank3 = console.Sensor(trek2, 'TANK3')
        self.tank4 = console.Sensor(trek2, 'TANK4')


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.ui_YesNoSeg = tester.Measurement(
            limits['Notify'], sense.oYesNoSeg)
        self.ui_YesNoBklight = tester.Measurement(
            limits['Notify'], sense.oYesNoBklight)
        self.ui_YesNoDisplay = tester.Measurement(
            limits['Notify'], sense.oYesNoDisplay)
        self.ui_YesNoLevel = tester.Measurement(
            limits['Notify'], sense.oYesNoLevel)
        tank_sensors = (
            sense.tank1, sense.tank2, sense.tank3, sense.tank4)
        self.tank1 = []
        lim = limits['Tank1']
        for sens in tank_sensors:
            self.tank1.append(tester.Measurement(lim, sens))
        self.tank2 = []
        lim = limits['Tank2']
        for sens in tank_sensors:
            self.tank2.append(tester.Measurement(lim, sens))
        self.tank3 = []
        lim = limits['Tank3']
        for sens in tank_sensors:
            self.tank3.append(tester.Measurement(lim, sens))
        self.tank4 = []
        lim = limits['Tank4']
        for sens in tank_sensors:
            self.tank4.append(tester.Measurement(lim, sens))
