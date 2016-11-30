#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMR-SBP ALL Test Program."""

import os
import inspect
from pydispatch import dispatcher
import share
import tester
from . import limit
from . import cmrsbp


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Vchg = tester.DCSource(devices['DCS1'])
        self.dcs_Vcom = tester.DCSource(devices['DCS2'])
        dcs_vbat1 = tester.DCSource(devices['DCS3'])
        dcs_vbat2 = tester.DCSource(devices['DCS4'])
        dcs_vbat3 = tester.DCSource(devices['DCS5'])
        self.dcs_vbat = tester.DCSourceParallel(
            (dcs_vbat1, dcs_vbat2, dcs_vbat3,))
        self.dcl_ibat = tester.DCLoad(devices['DCL1'])
        self.rla_vbat = tester.Relay(devices['RLA5'])
        self.rla_PicReset = tester.Relay(devices['RLA6'])
        self.rla_Prog = tester.Relay(devices['RLA7'])
        self.rla_EVM = tester.Relay(devices['RLA8'])    # Enables the EV2200
        self.rla_Pic = tester.Relay(devices['RLA9'])    # Connect to PIC
        # Apply 5V to Vdd for Erasing PIC
        self.rla_Erase = tester.Relay(devices['RLA10'])
        # Serial connection to data monitor
        self.cmr_ser = tester.SimSerial(
            simulation=self._fifo,
            port=limit.CMR_PORT, baudrate=9600, timeout=0.1)
        self.cmr = cmrsbp.CmrSbp(self.cmr_ser, data_timeout=10.0)
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            limit.PIC_HEX, folder, '18F252', self.rla_Prog)


    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_vbat, self.dcs_Vchg, self.dcs_Vcom):
            dcs.output(0.0, False)
        self.dcl_ibat.output(0.0)
        for rla in (self.rla_Pic, self.rla_Erase):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oMirvbatIn = sensor.Mirror()
        self.oMirCycleCnt = sensor.Mirror()
        self.oMirRelrnFlg = sensor.Mirror()
        self.oMirSenseRes = sensor.Mirror()
        self.oMirCapacity = sensor.Mirror()
        self.oMirRelStateCharge = sensor.Mirror()
        self.oMirHalfCell = sensor.Mirror()
        self.oMirVFCcalStatus = sensor.Mirror()
        self.oMirVChge = sensor.Mirror()
        self.oMirErrV = sensor.Mirror()
        self.oMirErrI = sensor.Mirror()
        self.oMirTemp = sensor.Mirror()
        self.oMirSw = sensor.Mirror()
        self.oMirSerNum = sensor.Mirror(rdgtype=sensor.ReadingString)
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.ovbatIn = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.ovbat = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.0001)
        self.oVcc = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVchge = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self.oibat = sensor.Vdc(
            dmm, high=4, low=2, rng=0.1, res=0.000001, scale=100.0)
        self.sn_entry_ini = sensor.DataEntry(
            message=tester.translate('cmrsbp_sn', 'msgSnEntryIni'),
            caption=tester.translate('cmrsbp_sn', 'capSnEntry'))
        self.sn_entry_fin = sensor.DataEntry(
            message=tester.translate('cmrsbp_sn', 'msgSnEntryFin'),
            caption=tester.translate('cmrsbp_sn', 'capSnEntry'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirvbatIn.flush()
        self.oMirCycleCnt.flush()
        self.oMirRelrnFlg.flush()
        self.oMirSenseRes.flush()
        self.oMirCapacity.flush()
        self.oMirRelStateCharge.flush()
        self.oMirHalfCell.flush()
        self.oMirVFCcalStatus.flush()
        self.oMirVChge.flush()
        self.oMirErrV.flush()
        self.oMirErrI.flush()
        self.oMirTemp.flush()
        self.oMirSerNum.flush()


class MeasureInit():

    """Initial and SerDate Test Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        mes = tester.Measurement
        self.cmr_SenseRes = mes(limits['SenseRes'], sense.oMirSenseRes)
        self.cmr_Halfcell = mes(limits['Halfcell'], sense.oMirHalfCell)
        self.cmr_VChgeOn = mes(limits['VChgeOn'], sense.oMirVChge)
        self.bq_ErrVUncal = mes(limits['ErrVUncal'], sense.oMirErrV)
        self.bq_ErrIUncal = mes(limits['ErrIUncal'], sense.oMirErrI)
        self.bq_Temp = mes(limits['BQ-Temp'], sense.oMirTemp)
        self.bq_ErrVCal = mes(limits['ErrVCal'], sense.oMirErrV)
        self.bq_ErrICal = mes(limits['ErrICal'], sense.oMirErrI)
        self.dmm_NoFinal = mes(
            limits['Final Not Connected'], sense.ovbatIn)
        self.dmm_vbat = mes(limits['Vbat'], sense.ovbat)
        self.dmm_vbatChge = mes(limits['VbatCharge'], sense.ovbat)
        self.dmm_Vcc = mes(limits['Vcc'], sense.oVcc)
        self.dmm_VErase = mes(limits['VErase'], sense.oVcc)
        self.dmm_Vchge = mes(limits['Vchge'], sense.oVchge)
        self.dmm_ibat = mes(limits['Ibat'], sense.oibat)
        self.ui_SnEntry = mes(limits['SerNum'], sense.sn_entry_ini)


class MeasureFin():

    """Final Test Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        mes = tester.Measurement
        self.ui_SnEntry = mes(limits['SerNum'], sense.sn_entry_fin)
        self.dmm_vbatIn = mes(limits['VbatIn'], sense.ovbatIn)
        self.cmr_vbatIn = mes(limits['VbatIn'], sense.oMirvbatIn)
        self.cmr_ErrV = mes(limits['ErrV'], sense.oMirErrV)
        self.cmr_CycleCnt = mes(limits['CycleCnt'], sense.oMirCycleCnt)
        self.cmr_RelrnFlg = mes(limits['RelrnFlg'], sense.oMirRelrnFlg)
        self.cmr_Sw = mes(limits['RotarySw'], sense.oMirSw)
        self.cmr_SenseRes = mes(limits['SenseRes'], sense.oMirSenseRes)
        self.cmr_Capacity = mes(limits['Capacity'], sense.oMirCapacity)
        self.cmr_RelStateCharge = mes(
            limits['StateOfCharge'], sense.oMirRelStateCharge)
        self.cmr_Halfcell = mes(limits['Halfcell'], sense.oMirHalfCell)
        self.cmr_VFCcalStatus = mes(
            limits['VFCcalStatus'], sense.oMirVFCcalStatus)
        self.cmr_SerNum = mes(limits['SerNumChk'], sense.oMirSerNum)


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
        self.pwrup = tester.SubStep((
            tester.MeasureSubStep((m.dmm_NoFinal, ), timeout=5),
            tester.RelaySubStep(((d.rla_vbat, True), )),
            tester.DcSubStep(setting=((d.dcs_vbat, 12.20), ), output=True),
            tester.MeasureSubStep((m.dmm_vbat, m.dmm_Vcc, ), timeout=5),
            ))
        # PowerComms: Power Comms, connect.
        self.pwr_comms = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Vcom, 12.0), ), output=True),
            tester.DcSubStep(
                setting=((d.dcs_Vchg, 12.6), ), output=True, delay=15),
            tester.RelaySubStep(((d.rla_Pic, True), ), delay=2),
            ))
        # CheckVcharge: Switch off vbat, measure
        self.chk_vch = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_vbat, 0.0), )),
            tester.RelaySubStep(((d.rla_vbat, False), )),
            tester.MeasureSubStep((m.dmm_vbatChge, m.dmm_Vcc), timeout=5),
            tester.RelaySubStep(((d.rla_vbat, True), )),
            ))
        # CalSetup:
        self.cal_setup = tester.SubStep((
            tester.DcSubStep(
                setting=((d.dcs_vbat, 12.20), (d.dcs_Vchg, 0.0))),
            tester.RelaySubStep(
                ((d.rla_Pic, False), (d.rla_PicReset, True), ), delay=2),
            tester.RelaySubStep(((d.rla_EVM, True), )),
            ))
