#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Test Program."""

import os
import time
import tester
from tester.testlimit import lim_hilo_delta, lim_hilo_int, lim_boolean
import share
from . import console

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
CAN_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('Vin', 12.0, 0.5),
    lim_boolean('Notify', True),
    lim_hilo_int('ARM-level1', 1),
    lim_hilo_int('ARM-level2', 2),
    lim_hilo_int('ARM-level3', 3),
    lim_hilo_int('ARM-level4', 4),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Final(tester.TestSequence):

    """Trek2 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('TunnelOpen', self._step_tunnel_open),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('TestTanks', self._step_test_tanks),
            )
        self._limits = LIMITS
        global d, s, m
        d = LogicalDevices(self.physical_devices, self.fifo)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        global d, s, m
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        # Switch on the USB hub & Serial ports
        d.dcs_Vcom.output(12.0, output=True)
        d.dcs_Vin.output(12.0, output=True)
        time.sleep(9)           # Wait for CAN binding to finish

    def _step_tunnel_open(self):
        """Open console tunnel."""
        if self.fifo:
            d.tunnel.port.puts('0 ECHO -> \r\n> ', preflush=1)
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('0x10000000\r\n')
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('\r\n')
            d.tunnel.port.puts('RRC,32,3,3,0,16,1\r\n')
        d.trek2.puts('0x10000000')
        d.trek2.puts('')

        d.trek2.open()
        d.trek2.testmode(True)

    def _step_display(self):
        """Display tests."""
        for sens in (s.oYesNoSeg, s.oYesNoBklight, ):
            self.fifo_push(((sens, True), ))
        d.trek2.puts('0x10000000')
        d.trek2.puts('')

        tester.MeasureGroup((m.ui_YesNoSeg, m.ui_YesNoBklight, ))
        d.trek2.testmode(False)

    def _step_test_tanks(self):
        """Test all tanks one level at a time."""
        for sens in s.otanks:
            self.fifo_push(((sens, (1, 2, 3, 4)), ))
        d.trek2.puts('')
        d.trek2.puts('')

        d.trek2['CONFIG'] = 0x7E00      # Enable all 4 tanks
        d.trek2['TANK_SPEED'] = 0.1     # Change update interval
        # No sensors - Tanks empty!
        tester.MeasureGroup(m.arm_level1, timeout=12)
        # 1 sensor
        d.rla_s1.set_on()
        tester.MeasureGroup(m.arm_level2, timeout=12)
        # 2 sensors
        d.rla_s2.set_on()
        tester.MeasureGroup(m.arm_level3, timeout=12)
        # 3 sensors
        d.rla_s3.set_on()
        tester.MeasureGroup(m.arm_level4, timeout=12)


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
        ser_can.port = CAN_PORT
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
