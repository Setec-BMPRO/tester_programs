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
import share.bp35

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
        self.dcl_out = dcload.DCLoad(devices['DCL1'])
        self.dcl_bat = dcload.DCLoad(devices['DCL5'])
        self.rla_reset = relay.Relay(devices['RLA1'])   # ON == Asserted
        self.rla_boot = relay.Relay(devices['RLA2'])    # ON == Asserted
        self.rla_pic = relay.Relay(devices['RLA3'])    # Connect PIC programmer.
        self.rla_loadsw = relay.Relay(devices['RLA4'])
        self.rla_vbat = relay.Relay(devices['RLA5'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Sources
        for dcs in (self.dcs_vbat, self.dcs_vaux):
            dcs.output(0.0, False)
        # Switch off DC Loads
        for ld in (self.dcl_out, self.dcl_bat):
            ld.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_reset, self.rla_boot, self.rla_pic,
                    self.rla_loadsw, self.rla_vbat):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, bp35):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm

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
        self.oVpfc = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
        self.oVout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self.o12Vpri = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.oFan = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self.o5Vusb = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.01)
        self.o15Vs = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.o3V3prog = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self.ARM_SwVer = share.bp35.Sensor(
            bp35, 'SwVer', rdgtype=tester.sensor.ReadingString)
        self.ARM_Fan = share.bp35.Sensor(bp35, 'FAN')
        self.ARM_Ld1I = share.bp35.Sensor(bp35, 'LOAD_1')
        self.ARM_Ld2I = share.bp35.Sensor(bp35, 'LOAD_2')
        self.ARM_Ld3I = share.bp35.Sensor(bp35, 'LOAD_3')
        self.ARM_Ld4I = share.bp35.Sensor(bp35, 'LOAD_4')
        self.ARM_Ld5I = share.bp35.Sensor(bp35, 'LOAD_5')
        self.ARM_Ld6I = share.bp35.Sensor(bp35, 'LOAD_6')
        self.ARM_Ld7I = share.bp35.Sensor(bp35, 'LOAD_7')
        self.ARM_Ld8I = share.bp35.Sensor(bp35, 'LOAD_8')
        self.ARM_Ld9I = share.bp35.Sensor(bp35, 'LOAD_9')
        self.ARM_Ld10I = share.bp35.Sensor(bp35, 'LOAD_10')
        self.ARM_Ld11I = share.bp35.Sensor(bp35, 'LOAD_11')
        self.ARM_Ld12I = share.bp35.Sensor(bp35, 'LOAD_12')
        self.ARM_Ld13I = share.bp35.Sensor(bp35, 'LOAD_13')
        self.ARM_Ld14I = share.bp35.Sensor(bp35, 'LOAD_14')
        self.ARM_BattI = share.bp35.Sensor(bp35, 'BATT_I')
        self.ARM_Vout = share.bp35.Sensor(bp35, 'BUS_V')
        self.ARM_CANID = share.bp35.Sensor(
            bp35, 'CAN_ID', rdgtype=tester.sensor.ReadingString)
        self.ARM_CANBIND = share.bp35.Sensor(bp35, 'CAN_BIND')

        self.oOutOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_out, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=30.0, stop=37.0, step=0.2, delay=0.1)
        self.oBatOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_bat, sensor=self.oVbat,
            detect_limit=(limits['InOCP'], ),
            start=18.0, stop=22.0, step=0.2, delay=0.1)
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
        self.oSnEntry = sensor.DataEntry(
            message=translate('msgSnEntry'),
            caption=translate('capSnEntry'))

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

        self.dmm_lock = Measurement(limits['FixtureLock'], sense.oLock)
        self.dmm_sw1 = Measurement(limits['SwShort'], sense.osw1)
        self.dmm_sw2 = Measurement(limits['SwShort'], sense.osw2)
        self.dmm_sw3 = Measurement(limits['SwShort'], sense.osw3)
        self.dmm_sw4 = Measurement(limits['SwShort'], sense.osw4)
        self.dmm_acin = Measurement(limits['ACin'], sense.oACin)
        self.dmm_vpfc = Measurement(limits['Vpfc'], sense.oVpfc)
        self.dmm_12Vpri = Measurement(limits['12Vpri'], sense.o12Vpri)
        self.dmm_5Vusb = Measurement(limits['5Vusb'], sense.o5Vusb)
        self.dmm_15Vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_voutFl = Measurement(limits['VoutFl'], sense.oVout)
        self.dmm_voutOff = Measurement(limits['VoutOff'], sense.oVout)
        self.dmm_vbatin = Measurement(limits['VbatIn'], sense.oVbat)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_fanOn = Measurement(limits['FanOn'], sense.oFan)
        self.dmm_fanOff = Measurement(limits['FanOff'], sense.oFan)
        self.dmm_3V3prog = Measurement(limits['3V3prog'], sense.o3V3prog)
        self.ramp_outOCP = Measurement(limits['OutOCP'], sense.oOutOCP)
        self.ramp_batOCP = Measurement(limits['BatOCP'], sense.oBatOCP)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoRed = Measurement(limits['Notify'], sense.oYesNoRed)
        self.ui_YesNoOrange = Measurement(limits['Notify'], sense.oYesNoOrange)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.arm_SwVer = Measurement(limits['ARM-SwVer'], sense.ARM_SwVer)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.ARM_Vout)
        self.arm_fan = Measurement(limits['ARM-Fan'], sense.ARM_Fan)
        self.arm_ld1I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld1I)
        self.arm_ld2I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld2I)
        self.arm_ld3I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld3I)
        self.arm_ld4I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld4I)
        self.arm_ld5I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld5I)
        self.arm_ld6I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld6I)
        self.arm_ld7I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld7I)
        self.arm_ld8I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld8I)
        self.arm_ld9I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld9I)
        self.arm_ld10I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld10I)
        self.arm_ld11I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld11I)
        self.arm_ld12I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld12I)
        self.arm_ld13I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld13I)
        self.arm_ld14I = Measurement(limits['ARM-LoadI'], sense.ARM_Ld14I)
        self.arm_battI = Measurement(limits['ARM-BattI'], sense.ARM_BattI)
        self.arm_can_id = Measurement(limits['CAN_ID'], sense.ARM_CANID)
        self.arm_can_bind = Measurement(limits['CAN_BIND'], sense.ARM_CANBIND)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements

        # OCP:
        bin1 = BinarySubStep(((d.dcl_out, 0.0, 30.0, 5.0), ), output=True)
        msr1 = MeasureSubStep((m.ramp_outOCP, ))
        ld2 = LoadSubStep(((d.dcl_out, 0.0), ), )
        dcs1 = DcSubStep(setting=((d.dcs_vbat, 12.8), ))  # Simulate a battery
        rly1 = RelaySubStep(((d.rla_vbat, True), ))
        msr2 = MeasureSubStep((m.dmm_vbat, ), timeout=5)
        bin2 = BinarySubStep(((d.dcl_bat, 0.0, 18.0, 5.0), ), output=True)
        msr3 = MeasureSubStep((m.ramp_batOCP, ))
        rly2 = RelaySubStep(((d.rla_vbat, False), ))
        dcs2 = DcSubStep(setting=((d.dcs_vbat, 0.0), ))
        self.ocp = Step(
            (bin1, msr1, ld2, dcs1, rly1, msr2, bin2, msr3, rly2, dcs2))

        # Shutdown: Shutdown, recovery, check load switch.
        ld1 = LoadSubStep(((d.dcl_out, 39.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_voutOff, ), timeout=10)
        ld2 = LoadSubStep(((d.dcl_out, 0.0), ), )
        msr2 = MeasureSubStep((m.dmm_vout, m.dmm_vbat,), timeout=20)
        rly1 = RelaySubStep(((d.rla_loadsw, True), ))
        msr3 = MeasureSubStep((m.dmm_voutOff, ), timeout=5)
        rly2 = RelaySubStep(((d.rla_loadsw, False), ))
        msr4 = MeasureSubStep((m.dmm_vout, ), timeout=5)
        self.shdn = Step((ld1, msr1, ld2, msr2, rly1, msr3, rly2, msr4))
