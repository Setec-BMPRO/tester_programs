#!/usr/bin/env python3
"""BP35 Initial Test Program.

        Logical Devices
        Sensors
        Measurements

"""
from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *

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
        self.acsource = acsource.ACSource(devices['ACS'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_vcom = dcsource.DCSource(devices['DCS1'])  # Power RS232 + Fixture Trek2.
        self.dcs_vbat = dcsource.DCSource(devices['DCS2'])  # Power for programming.
        self.dcs_vaux = dcsource.DCSource(devices['DCS3'])
        dcl_vout = dcload.DCLoad(devices['DCL1'])
        dcl_vbat = dcload.DCLoad(devices['DCL5'])
        self.dcl = dcload.DCLoadParallel(((dcl_vout, 29), (dcl_vbat, 14)))
        self.rla_reset = relay.Relay(devices['RLA1'])   # ON == Asserted
        self.rla_boot = relay.Relay(devices['RLA2'])    # ON == Asserted
        self.rla_pic = relay.Relay(devices['RLA3'])    # Connect PIC programmer.
        self.rla_loadsw = relay.Relay(devices['RLA4'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Sources
        for dcs in (self.dcs_vcom, self.dcs_vbat, self.dcs_vaux):
            dcs.output(0.0, False)
        # Switch off DC Loads
        for ld in (self.dcl, ):
            ld.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_reset, self.rla_boot, self.rla_pic,
                   self.rla_loadsw):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, bp35):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        dcl = logical_devices.dcl

        self.oMirPIC = sensor.Mirror()
        self.oMirARM = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)

        self.oLock = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self.osw1 = sensor.Res(dmm, high=17, low=7, rng=1000000, res=1)
        self.osw2 = sensor.Res(dmm, high=18, low=7, rng=1000000, res=1)
        self.osw3 = sensor.Res(dmm, high=19, low=7, rng=1000000, res=1)
        self.osw4 = sensor.Res(dmm, high=19, low=8, rng=1000000, res=1)
        self.oACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.oVout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self.o12Vpri = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.oFan = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self.o5Vusb = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.01)
        self.o15Vs = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.o3V3prog = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=dcl, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=39.0, step=0.2, delay=0.1)
        tester.TranslationContext = 'bp35_initial'
        self.oYesNoGreen = sensor.YesNo(
            message=translate('IsLedGreen?'),
            caption=translate('capGreenLed'))
        self.oYesNoRed = sensor.YesNo(
            message=translate('IsLedRed?'),
            caption=translate('capRedLed'))
        self.oYesNoOrange = sensor.YesNo(
            message=translate('IsLedOrange?'),
            caption=translate('capOrangeLed'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirPIC.flush()
        self.oMirARM.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.pgmPIC = Measurement(limits['Program'], sense.oMirPIC)
        self.pgmARM = Measurement(limits['Program'], sense.oMirARM)

        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.oLock)
        self.dmm_sw1 = Measurement(limits['SwShort'], sense.osw1)
        self.dmm_sw2 = Measurement(limits['SwShort'], sense.osw2)
        self.dmm_sw3 = Measurement(limits['SwShort'], sense.osw3)
        self.dmm_sw4 = Measurement(limits['SwShort'], sense.osw4)
        self.dmm_ACin = Measurement(limits['ACin'], sense.oACin)
        self.dmm_Vbus = Measurement(limits['Vbus'], sense.oVbus)
        self.dmm_12Vpri = Measurement(limits['12Vpri'], sense.o12Vpri)
        self.dmm_5Vusb = Measurement(limits['5Vusb'], sense.o5Vusb)
        self.dmm_15Vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_VoutFl = Measurement(limits['VoutFl'], sense.oVout)
        self.dmm_VoutOff = Measurement(limits['VoutOff'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_FanOn = Measurement(limits['FanOn'], sense.oFan)
        self.dmm_FanOff = Measurement(limits['FanOff'], sense.oFan)
        self.dmm_3V3prog = Measurement(limits['3V3prog'], sense.o3V3prog)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoRed = Measurement(limits['Notify'], sense.oYesNoRed)
        self.ui_YesNoOrange = Measurement(limits['Notify'], sense.oYesNoOrange)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements

        # PowerUp:
        dcs1 = DcSubStep(setting=((d.dcs_vbat, 0.0), ))
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=1)
        msr1 = MeasureSubStep((m.dmm_ACin, m.dmm_Vbus, m.dmm_12Vpri,
                               m.dmm_5Vusb, m.dmm_3V3, m.dmm_15Vs,
                               m.dmm_Vout, m.dmm_Vbat), timeout=5)
        ld1 = LoadSubStep(((d.dcl, 1.0), ), output=True)
        msr2 = MeasureSubStep((m.dmm_Vout, m.dmm_Vbat,), timeout=5)
        ld2 = LoadSubStep(((d.dcl, 0.0), ))
        self.pwr_up = Step((dcs1, acs1, msr1, ld1, msr2, ld2))

        # Shutdown: Shutdown, recovery, check load switch.
        ld1 = LoadSubStep(((d.dcl, 39.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_VoutOff, ), timeout=10)
        ld2 = LoadSubStep(((d.dcl, 0.0), ), )
        msr2 = MeasureSubStep((m.dmm_Vout, m.dmm_Vbat,), timeout=10)
        rly1 = RelaySubStep(((d.rla_loadsw, True), ))
        msr3 = MeasureSubStep((m.dmm_VoutOff, ), timeout=5)
        rly2 = RelaySubStep(((d.rla_loadsw, False), ))
        msr4 = MeasureSubStep((m.dmm_Vout, ), timeout=5)
        self.shdn = Step((ld1, msr1, ld2, msr2, rly1, msr3, rly2, msr4))
