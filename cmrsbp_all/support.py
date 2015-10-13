#!/usr/bin/env python3
"""CMR-SBP ALL Test Program."""

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
        self.dcs_Vchg = dcsource.DCSource(devices['DCS1'])
        self.dcs_Vcom = dcsource.DCSource(devices['DCS2'])
        dcs_vbat1 = dcsource.DCSource(devices['DCS3'])
        dcs_vbat2 = dcsource.DCSource(devices['DCS4'])
        dcs_vbat3 = dcsource.DCSource(devices['DCS5'])
        self.dcs_vbat = dcsource.DCSourceParallel(
            (dcs_vbat1, dcs_vbat2, dcs_vbat3,))
        self.dcl_ibat = dcload.DCLoad(devices['DCL1'])
        self.rla_Bit0 = relay.Relay(devices['RLA1'])
        self.rla_Bit1 = relay.Relay(devices['RLA2'])
        self.rla_Bit2 = relay.Relay(devices['RLA3'])
        self.rla_Bit3 = relay.Relay(devices['RLA4'])
        self.rla_vbat = relay.Relay(devices['RLA5'])
        self.rla_PicReset = relay.Relay(devices['RLA6'])
        self.rla_Prog = relay.Relay(devices['RLA7'])
        self.rla_EVM = relay.Relay(devices['RLA8'])    # Enables the EV2200
        self.rla_Pic = relay.Relay(devices['RLA9'])    # Connect to PIC
        # Apply 5V to Vdd for Erasing PIC
        self.rla_Erase = relay.Relay(devices['RLA10'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_vbat, self.dcs_Vchg, self.dcs_Vcom):
            dcs.output(0.0, False)
        self.dcs_Vcom.output(0.0, False)
        # Switch off DC Load
        self.dcl_ibat.output(0.0)
        # Switch off all Relays
        for rla in (self.rla_Bit0, self.rla_Bit1, self.rla_Bit2,
                    self.rla_Bit3, self.rla_Pic, self.rla_Erase):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirvbatIn = sensor.Mirror()
        self.oMirCycleCnt = sensor.Mirror()
        self.oMirRelrnFlg = sensor.Mirror()
        self.oMirSw = sensor.Mirror()
        self.oMirSenseRes = sensor.Mirror()
        self.oMirCapacity = sensor.Mirror()
        self.oMirRelStateCharge = sensor.Mirror()
        self.oMirHalfCell = sensor.Mirror()
        self.oMirVFCcalStatus = sensor.Mirror()
        self.oMirPIC = sensor.Mirror()
        self.oMirVChge = sensor.Mirror()
        self.oMirErrV = sensor.Mirror()
        self.oMirErrI = sensor.Mirror()
        self.oMirTemp = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        self.ovbatIn = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.ovbat = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.0001)
        self.oVcc = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVchge = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self.oibat = sensor.Vdc(
            dmm, high=4, low=2, rng=0.1, res=0.000001, scale=100.0)
        self.oSnEntry = sensor.DataEntry(
            message=translate('cmrsbp_sn', 'msgSnEntry'),
            caption=translate('cmrsbp_sn', 'capSnEntry'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirvbatIn.flush()
        self.oMirCycleCnt.flush()
        self.oMirRelrnFlg.flush()
        self.oMirSw.flush()
        self.oMirSenseRes.flush()
        self.oMirCapacity.flush()
        self.oMirRelStateCharge.flush()
        self.oMirHalfCell.flush()
        self.oMirVFCcalStatus.flush()
        self.oMirPIC.flush()
        self.oMirVChge.flush()
        self.oMirErrV.flush()
        self.oMirErrI.flush()
        self.oMirTemp.flush()


class MeasureInit():

    """Initial and SerDate Test Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.pgmPIC = Measurement(limits['Program'], sense.oMirPIC)
        self.cmr_SenseRes = Measurement(limits['SenseRes'], sense.oMirSenseRes)
        self.cmr_Halfcell = Measurement(limits['Halfcell'], sense.oMirHalfCell)
        self.cmr_VChgeOff = Measurement(limits['VChgeOff'], sense.oMirVChge)
        self.cmr_VChgeOn = Measurement(limits['VChgeOn'], sense.oMirVChge)
        self.cmr_Sw02 = Measurement(limits['Bits0+2'], sense.oMirSw)
        self.cmr_Sw13 = Measurement(limits['Bits1+3'], sense.oMirSw)
        self.cmr_SwOff = Measurement(limits['BitsOff'], sense.oMirSw)
        self.bq_ErrVUncal = Measurement(limits['ErrVUncal'], sense.oMirErrV)
        self.bq_ErrIUncal = Measurement(limits['ErrIUncal'], sense.oMirErrI)
        self.bq_Temp = Measurement(limits['BQ-Temp'], sense.oMirTemp)
        self.bq_ErrVCal = Measurement(limits['ErrVCal'], sense.oMirErrV)
        self.bq_ErrICal = Measurement(limits['ErrICal'], sense.oMirErrI)
        self.dmm_NoFinal = Measurement(
            limits['Final Not Connected'], sense.ovbatIn)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.ovbat)
        self.dmm_vbatChge = Measurement(limits['VbatCharge'], sense.ovbat)
        self.dmm_Vcc = Measurement(limits['Vcc'], sense.oVcc)
        self.dmm_VErase = Measurement(limits['VErase'], sense.oVcc)
        self.dmm_Vchge = Measurement(limits['Vchge'], sense.oVchge)
        self.dmm_ibat = Measurement(limits['Ibat'], sense.oibat)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)


class MeasureFin():

    """Final Test Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_vbatIn = Measurement(limits['VbatIn'], sense.ovbatIn)
        self.cmr_vbatIn = Measurement(limits['VbatIn'], sense.oMirvbatIn)
        self.cmr_ErrV = Measurement(limits['ErrV'], sense.oMirErrV)
        self.cmr_CycleCnt = Measurement(limits['CycleCnt'], sense.oMirCycleCnt)
        self.cmr_RelrnFlg = Measurement(limits['RelrnFlg'], sense.oMirRelrnFlg)
        self.cmr_Sw = Measurement(limits['RotarySw'], sense.oMirSw)
        self.cmr_SenseRes = Measurement(limits['SenseRes'], sense.oMirSenseRes)
        self.cmr_Capacity = Measurement(limits['Capacity'], sense.oMirCapacity)
        self.cmr_RelStateCharge = Measurement(
            limits['StateOfCharge'], sense.oMirRelStateCharge)
        self.cmr_Halfcell = Measurement(limits['Halfcell'], sense.oMirHalfCell)
        self.cmr_VFCcalStatus = Measurement(
            limits['VFCcalStatus'], sense.oMirVFCcalStatus)


class SubTestInit():

    """Initial and SerDate SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp: Check, Apply Batt In, measure.
        msr1 = MeasureSubStep((m.dmm_NoFinal, ), timeout=5)
        rly1 = RelaySubStep(((d.rla_Bit0, True), (d.rla_vbat, True), ))
        rly2 = RelaySubStep(((d.rla_vbat, True), ))
        rly3 = RelaySubStep(((d.rla_PicReset, True), ), delay=2)
        rly4 = RelaySubStep(((d.rla_EVM, True), ))
        dcs1 = DcSubStep(setting=((d.dcs_vbat, 12.20), ), output=True)
        msr2 = MeasureSubStep((m.dmm_vbat, m.dmm_Vcc, ), timeout=5)
        self.pwrup = Step((msr1, rly1, dcs1, msr2))
        self.pwrup_sd = Step((msr1, rly2, dcs1, rly3, rly4))
        # PowerComms: Power Comms, connect.
        dcs1 = DcSubStep(
            setting=((d.dcs_Vcom, 12.0), ), output=True, delay=15)
        rly1 = RelaySubStep(
            ((d.rla_Bit0, False), (d.rla_Pic, True)), delay=2)
        self.pwr_comms = Step((dcs1, rly1))
        # RotarySw: Simulate Bits 0/2 on, 1/3 on and all off.
        dcs1 = DcSubStep(setting=((d.dcs_Vchg, 12.6), ), output=True)
        rly1 = RelaySubStep(
            ((d.rla_Bit0, True), (d.rla_Bit2, True), (d.rla_Bit1, False),
             (d.rla_Bit3, False)), delay=15)
        rly2 = RelaySubStep(
            ((d.rla_Bit1, True), (d.rla_Bit3, True), (d.rla_Bit0, False),
             (d.rla_Bit2, False)), delay=15)
        rly3 = RelaySubStep(
            ((d.rla_Bit0, False), (d.rla_Bit1, False), (d.rla_Bit2, False),
             (d.rla_Bit3, False)), delay=15)
        self.sw02 = Step((dcs1, rly1))
        self.sw13 = Step((rly2, ))
        self.swoff = Step((rly3, ))
        # CheckVcharge: Switch off vbat, measure
        dcs1 = DcSubStep(setting=((d.dcs_vbat, 0.0), ))
        rly1 = RelaySubStep(((d.rla_vbat, False), ))
        msr1 = MeasureSubStep((m.dmm_vbatChge, m.dmm_Vcc), timeout=5)
        rly2 = RelaySubStep(((d.rla_vbat, True), ))
        self.chk_vch = Step((dcs1, rly1, msr1, rly2))
        # CalSetup:
        dcs1 = DcSubStep(setting=((d.dcs_vbat, 12.20), (d.dcs_Vchg, 0.0)))
        rly1 = RelaySubStep(
            ((d.rla_Pic, False), (d.rla_PicReset, True), ), delay=2)
        rly2 = RelaySubStep(((d.rla_EVM, True), ))
        self.cal_setup = Step((dcs1, rly1, rly2))


class SubTestFin():

    """Final SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        # StartUp:  Power comms, connect.
        dcs1 = DcSubStep(
            setting=((d.dcs_Vcom, 12.0), ), output=True, delay=1)
        rly1 = RelaySubStep(((d.rla_Pic, True), ))
        self.startup = Step((dcs1, rly1))
