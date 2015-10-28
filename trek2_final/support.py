#!/usr/bin/env python3
"""Trek2 Final Test Program.

        Logical Devices
        Sensors
        Measurements

"""

import tester
from tester.devlogical import *
from tester.measure import *
import share.trek2

sensor = tester.sensor
translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        # Power RS232 + Fixture Trek2.
        self.dcs_Vcom = dcsource.DCSource(devices['DCS1'])
        # Power unit under test.
        self.dcs_Vin = dcsource.DCSource(devices['DCS2'])
        # As the water level rises the "switches" close. The order of switch
        # closure does not matter, just the number closed.
        # The lowest bar always flashes. Closing these relays makes the other
        # bars come on.
        self.rla_s1 = relay.Relay(devices['RLA3'])    # ON == Asserted
        self.rla_s2 = relay.Relay(devices['RLA4'])    # ON == Asserted
        self.rla_s3 = relay.Relay(devices['RLA5'])    # ON == Asserted

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_Vin, self.dcs_Vcom):
            dcs.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_s1, self.rla_s2, self.rla_s3):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, trek2):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.oYesNoSeg = sensor.YesNo(
            message=translate('trek2_final', 'AreSegmentsOn?'),
            caption=translate('trek2_final', 'capSegments'))
        self.oYesNoBklight = sensor.YesNo(
            message=translate('trek2_final', 'IsBacklightOk?'),
            caption=translate('trek2_final', 'capBacklight'))
        self.oYesNoDisplay = sensor.YesNo(
            message=translate('trek2_final', 'IsDisplayOk?'),
            caption=translate('trek2_final', 'capDisplay'))
        self.oYesNoLevel = sensor.YesNo(
            message=translate('trek2_final', 'IsLevelOk?'),
            caption=translate('trek2_final', 'capLevel'))
        self.tank1 = share.trek2.Sensor(trek2, 'TANK1')
        self.tank2 = share.trek2.Sensor(trek2, 'TANK2')
        self.tank3 = share.trek2.Sensor(trek2, 'TANK3')
        self.tank4 = share.trek2.Sensor(trek2, 'TANK4')


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.ui_YesNoSeg = Measurement(
            limits['Notify'], sense.oYesNoSeg)
        self.ui_YesNoBklight = Measurement(
            limits['Notify'], sense.oYesNoBklight)
        self.ui_YesNoDisplay = Measurement(
            limits['Notify'], sense.oYesNoDisplay)
        self.ui_YesNoLevel = Measurement(
            limits['Notify'], sense.oYesNoLevel)
        tank_sensors = (
            sense.tank1, sense.tank2, sense.tank3, sense.tank4)
        self.tank0 = []
        lim = limits['Tank0']
        for sens in tank_sensors:
            self.tank0.append(Measurement(lim, sens))
        self.tank1 = []
        lim = limits['Tank1']
        for sens in tank_sensors:
            self.tank1.append(Measurement(lim, sens))
        self.tank2 = []
        lim = limits['Tank2']
        for sens in tank_sensors:
            self.tank2.append(Measurement(lim, sens))
        self.tank3 = []
        lim = limits['Tank3']
        for sens in tank_sensors:
            self.tank3.append(Measurement(lim, sens))


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        # PowerUp:
        dcs1 = DcSubStep(
            setting=((d.dcs_Vcom, 12.0), (d.dcs_Vin, 12.0)), output=True)
        self.pwr_up = Step((dcs1, ))
