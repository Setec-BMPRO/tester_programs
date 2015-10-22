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
        self.dcs_vcom = dcsource.DCSource(devices['DCS1'])
        self.dcs_vbat = dcsource.DCSource(devices['DCS2'])
        self.dcs_vaux = dcsource.DCSource(devices['DCS3'])
        self.dcs_sreg = dcsource.DCSource(devices['DCS4'])
        self.dcl_out = dcload.DCLoad(devices['DCL1'])
        self.dcl_bat = dcload.DCLoad(devices['DCL5'])
        self.rla_reset = relay.Relay(devices['RLA1'])   # ON == Asserted
        self.rla_boot = relay.Relay(devices['RLA2'])    # ON == Asserted
        self.rla_pic = relay.Relay(devices['RLA3'])     # PIC programmer
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
        for dcs in (self.dcs_vbat, self.dcs_vaux, self.dcs_sreg):
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
        self.oVload = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self.oVsreg = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12Vpri = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.oFan = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self.o5Vusb = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.01)
        self.o15Vs = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.o3V3prog = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self.oBatOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_bat, sensor=self.oVbat,
            detect_limit=(limits['InOCP'], ),
            start=4.0, stop=10.0, step=0.5, delay=0.1)
        self.oSnEntry = sensor.DataEntry(
            message=translate('bp35_initial', 'msgSnEntry'),
            caption=translate('bp35_initial', 'capSnEntry'))
        self.ARM_SwVer = share.bp35.Sensor(
            bp35, 'SwVer', rdgtype=tester.sensor.ReadingString)
        self.ARM_AcV = share.bp35.Sensor(bp35, 'AC_V')
        self.ARM_AcF = share.bp35.Sensor(bp35, 'AC_F')
        self.ARM_PriT = share.bp35.Sensor(bp35, 'PRI_T')
        self.ARM_SecT = share.bp35.Sensor(bp35, 'SEC_T')
        self.ARM_Vout = share.bp35.Sensor(bp35, 'BUS_V')
        self.ARM_BattType = share.bp35.Sensor(bp35, 'BATT_TYPE')
        self.ARM_BattSw = share.bp35.Sensor(bp35, 'BATT_SWITCH')
        self.ARM_Fan = share.bp35.Sensor(bp35, 'FAN')
        self.ARM_CANID = share.bp35.Sensor(
            bp35, 'CAN_ID', rdgtype=tester.sensor.ReadingString)
        self.ARM_CANBIND = share.bp35.Sensor(bp35, 'CAN_BIND')
        self.ARM_CANSTATS = share.bp35.Sensor(bp35, 'CAN_STATS')
        # Generate 14 load current sensors
        self.ARM_Loads = []
        for i in range(1, 15):
            s = share.bp35.Sensor(bp35, 'LOAD_{}'.format(i))
            self.ARM_Loads.append(s)
        self.ARM_BattI = share.bp35.Sensor(bp35, 'BATT_I')
        self.ARM_AuxV = share.bp35.Sensor(bp35, 'AUX_V')
        self.ARM_AuxI = share.bp35.Sensor(bp35, 'AUX_I')

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
        self.dmm_vload = Measurement(limits['Vload'], sense.oVload)
        self.dmm_vloadOff = Measurement(limits['VloadOff'], sense.oVload)
        self.dmm_vbatin = Measurement(limits['VbatIn'], sense.oVbat)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_vsregpre = Measurement(limits['VsetPre'], sense.oVsreg)
        self.dmm_vsregpost = Measurement(limits['VsetPost'], sense.oVsreg)
        self.dmm_vaux = Measurement(limits['Vaux'], sense.oVbat)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_fanOn = Measurement(limits['FanOn'], sense.oFan)
        self.dmm_fanOff = Measurement(limits['FanOff'], sense.oFan)
        self.dmm_3V3prog = Measurement(limits['3V3prog'], sense.o3V3prog)
        self.ramp_batOCP = Measurement(limits['BatOCP'], sense.oBatOCP)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.arm_SwVer = Measurement(limits['ARM-SwVer'], sense.ARM_SwVer)
        self.arm_acv = Measurement(limits['ARM-AcV'], sense.ARM_AcV)
        self.arm_acf = Measurement(limits['ARM-AcF'], sense.ARM_AcF)
        self.arm_priT = Measurement(limits['ARM-PriT'], sense.ARM_PriT)
        self.arm_secT = Measurement(limits['ARM-SecT'], sense.ARM_SecT)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.ARM_Vout)
        self.arm_fan = Measurement(limits['ARM-Fan'], sense.ARM_Fan)
        self.arm_can_id = Measurement(limits['CAN_ID'], sense.ARM_CANID)
        self.arm_can_bind = Measurement(limits['CAN_BIND'], sense.ARM_CANBIND)
        self.arm_can_stats = Measurement(limits['CAN_STATS'], sense.ARM_CANSTATS)
        # Generate 14 load current measurements
        self.arm_loads = ()
        for sen in sense.ARM_Loads:
            m = Measurement(limits['ARM-LoadI'], sen)
            self.arm_loads += (m, )
        self.arm_battI = Measurement(limits['ARM-BattI'], sense.ARM_BattI)
        self.arm_auxV = Measurement(limits['ARM-AuxV'], sense.ARM_AuxV)
        self.arm_auxI = Measurement(limits['ARM-AuxI'], sense.ARM_AuxI)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
