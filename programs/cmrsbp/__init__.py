#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMR-SBP ALL Test Program."""
# FIXME: Upgrade this program to 3rd Generation standards with unittest.

import os
import datetime
import threading
import time
import inspect
from pydispatch import dispatcher
import tester
import share
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_int, lim_lo, lim_string, lim_boolean)
from . import ev2200
from . import cmrsbp

PIC_HEX = 'CMR-SBP-9.hex'

# Serial port for the EV2200.
EV_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Serial port for the CMR.
CMR_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM2'}[os.name]

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
LIMITS_INI = tester.testlimit.limitset((
    lim_hilo_delta('Vbat', 12.0, 0.10),
    lim_hilo('VbatCharge', 11.8, 12.5),
    lim_hilo_delta('Vcc', 3.3, 0.2),
    lim_hilo('VErase', 4.8, 5.05),
    lim_lo('IStart', 0.02),
    lim_hilo('Vchge', 12.8, 15.0),
    # 2.0A +/- 10mA
    lim_hilo_delta('Ibat', -2.00, 0.01),
    lim_lo('Final Not Connected', 1.0),
    lim_hilo_delta('SenseRes', 250, 30),
    lim_hilo_delta('Halfcell', 110, 10),
    lim_hilo_delta('VChgeOn', 350, 50),
    lim_hilo_delta('ErrVUncal', 0.0, 0.5),
    lim_hilo_delta('ErrVCal', 0.0, 0.03),
    lim_hilo_delta('ErrIUncal', 0.0, 0.060),
    lim_hilo_delta('ErrICal', 0.0, 0.015),
    # 298K nominal +/- 2.5K in Kelvin (25C +/- 2.5C in Celsius).
    lim_hilo_delta('BQ-Temp', 300, 4.5),
    # SerialDate
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C][0-9]{5}F[0-9]{4}$'),
    ))

_FIN_DATA = (   # Shared Final Test limits
    lim_hilo('VbatIn', 12.8, 15.0),
    lim_hilo_delta('ErrV', 0.0, 0.03),
    lim_hilo('CycleCnt', 0.5, 20.5),
    lim_boolean('RelrnFlg', False),
    lim_hilo_int('RotarySw', 256),
    lim_hilo_delta('Halfcell', 400, 50),
    lim_boolean('VFCcalStatus', True),
    lim_string('SerNumChk', ''),
    )

LIMITS_8 = tester.testlimit.limitset(_FIN_DATA + (
    lim_hilo('SenseRes', 39.0, 91.0),
    lim_hilo('Capacity', 6400, 11000),
    lim_hilo_delta('StateOfCharge', 100.0, 10.5),
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C](36861|40214)F[0-9]{4}$'),
    ))

LIMITS_13 = tester.testlimit.limitset(_FIN_DATA + (
    lim_hilo('SenseRes', 221.0, 280.0),
    lim_hilo('Capacity', 11000, 15000),
    lim_hilo_delta('StateOfCharge', 100.0, 10.5),
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C](36862|40166)F[0-9]{4}$'),
    ))

LIMITS_17 = tester.testlimit.limitset(_FIN_DATA + (
    lim_hilo('SenseRes', 400.0, 460.0),
    lim_hilo('Capacity', 15500, 20000),
    lim_lo('StateOfCharge', 30.0),
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C]403(15|23)F[0-9]{4}$'),
    ))

LIMITS = {      # Test limit selection keyed by program parameter
    None: LIMITS_13,
    '8': LIMITS_8,
    '13': LIMITS_13,
    '17': LIMITS_17,
    }

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class _Main(tester.TestSequence):

    """CMR-SBP Base Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        global d, s
        d = LogicalDevices(self.physical_devices, self.fifo)
        s = Sensors(d, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s
        d.cmr.close()
        d.cmr_ser.close()
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _read_data(self):
        """Read data broadcast from PIC.

        @return Dictionary of CMR data.

        """
        if self.fifo:
            _str = """
#BATTERY MODE,24576
#TEMPERATURE,297.0
#VOLTAGE,13.710
#CURRENT,0.0
#REL STATE OF CHARGE,{}
#ABS STATE OF CHARGE,0
#REMAINING CAPACITY,0
#FULL CHARGE CAPACITY,{}
#CHARGING CURRENT,0
#CHARGING VOLTAGE,0
#BATTERY STATUS,0
#CYCLE COUNT,1
#PACK STATUS AND CONFIG,-24416
#FULL PACK READING,0
#HALF CELL READING,{}
#SENSE RESISTOR READING,{}
#CHARGE INPUT READING,0
#ROTARY SWITCH READING,256
#SERIAL NUMBER,1234
"""
            soc = 100
            sense_res = 250
            full_charge = 13000
            half_cell = 110
            if self._isFin:
                half_cell = 397
                low, high = self._limits['SenseRes'].limit
                if low < 100:
                    sense_res = 50
                    full_charge = 8000
                if low > 300:
                    soc = 25
                    sense_res = 450
                    full_charge = 17000
            data_str = _str.format(soc, full_charge, half_cell, sense_res)
            def myputs():   # This will push the data when timer is done
                d.cmr_ser.puts(data_str)
            tmr = threading.Timer(0.5, myputs)
            tmr.start()     # Push data once we are inside _cmr.read()
        data = d.cmr.read()
        return data


class Initial(_Main):

    """CMR-SBP Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        self._limits = LIMITS_INI
        super().open()
        self._isFin = False
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('CheckPicValues', self._step_check_pic_vals),
            tester.TestStep('CheckVcharge', self._step_check_vchge),
            tester.TestStep('CalBQvolts', self._step_calv),
            tester.TestStep('CalBQcurrent', self._step_cali),
            )
        self._ev_ser = tester.SimSerial(
            simulation=self.fifo,
            port=EV_PORT, baudrate=9600, timeout=4.0)
        self._ev = ev2200.EV2200(self._ev_ser)
        global m
        m = MeasureInit(s, self._limits)

    def close(self):
        """Finished testing."""
        self._ev_ser.close()
        super().close()

    def _step_power_up(self):
        """Power up with vbat.

           Check that a Final Unit is not connected.
           Apply vbat and measure voltages.

        """
        self.fifo_push(((s.ovbatIn, 0.5), (s.ovbat, 12.0), (s.oVcc, 3.3), ))

        m.dmm_NoFinal.measure(timeout=5)
        d.rla_vbat.set_on()
        d.dcs_vbat.output(12.20, output=True)
        tester.MeasureGroup((m.dmm_vbat, m.dmm_Vcc, ), timeout=5)

    def _step_program(self):
        """Program the PIC micro.

           Apply 5.0V to Vdd.
           Program.

        """
        self.fifo_push(((s.oVcc, 5.0), ))

        d.rla_Erase.set_on()
        m.dmm_VErase.measure(timeout=5)
        d.program_pic.program()
        d.rla_Erase.set_off()

    def _step_check_pic_vals(self):
        """Check some values from the PIC.

           Power Comms interface and connect to PIC.
           Read PIC and check values.

        """
        d.dcs_Vcom.output(12.0, output=True)
        d.dcs_Vchg.output(12.6, output=True, delay=15)
        d.rla_Pic.set_on(delay=2)
        cmr_data = self._read_data()
        s.oMirSenseRes.store(cmr_data['SENSE RESISTOR READING'])
        s.oMirHalfCell.store(cmr_data['HALF CELL READING'])
        s.oMirVChge.store(cmr_data['CHARGE INPUT READING'])
        tester.MeasureGroup((m.cmr_SenseRes, m.cmr_Halfcell, m.cmr_VChgeOn),)

    def _step_check_vchge(self):
        """Check Vcharge."""
        self.fifo_push(((s.ovbat, 12.0), (s.oVcc, 3.3), ))

        d.dcs_vbat.output(0.0)
        d.rla_vbat.set_off()
        tester.MeasureGroup((m.dmm_vbatChge, m.dmm_Vcc), timeout=5)
        d.rla_vbat.set_on()

    def _step_calv(self):
        """Calibrate vbat for BQ2060A."""
        self.fifo_push(((s.ovbat, 12.0), ))

        d.dcs_vbat.output(12.20)
        d.dcs_Vchg.output(0.0)
        d.rla_Pic.set_off()
        d.rla_PicReset.set_on(delay=2)
        d.rla_EVM.set_on()
        dmm_vbat = m.dmm_vbat.measure(timeout=5).reading1
        ev_data = self._ev.read_vit()
        s.oMirErrV.store(dmm_vbat - ev_data['Voltage'])
        s.oMirTemp.store(ev_data['Temperature'])
        m.bq_ErrVUncal.measure()
        m.bq_Temp.measure()
        self._ev.cal_v(dmm_vbat)
        ev_data = self._ev.read_vit()
        s.oMirErrV.store(dmm_vbat - ev_data['Voltage'])
        m.bq_ErrVCal.measure()

    def _step_cali(self):
        """Calibrate ibat for BQ2060A."""
        self.fifo_push(((s.oibat, 0.02), ))

        d.dcl_ibat.output(2.0, True)
        dmm_ibat = m.dmm_ibat.measure(timeout=5).reading1
        time.sleep(3.0)
        ev_data = self._ev.read_vit()
        s.oMirErrI.store(dmm_ibat - ev_data['Current'])
        m.bq_ErrIUncal.measure()
        self._ev.cal_i(dmm_ibat)
        ev_data = self._ev.read_vit()
        s.oMirErrI.store(dmm_ibat - ev_data['Current'])
        m.bq_ErrICal.measure()
        d.dcl_ibat.output(0.0)


class SerialDate(_Main):

    """CMR-SBP SerialDate Test Program."""

    def open(self):
        """Prepare for testing."""
        self._limits = LIMITS_INI
        super().open()
        self._isFin = False
        self.steps = (
            tester.TestStep('SerialDate', self._step_sn_date),
            )
        self._ev_ser = tester.SimSerial(
            simulation=self.fifo,
            port=EV_PORT, baudrate=9600, timeout=4.0)
        self._ev = ev2200.EV2200(self._ev_ser)
        global m
        m = MeasureInit(s, self._limits)

    def close(self):
        """Finished testing."""
        self._ev_ser.close()
        super().close()

    def _step_sn_date(self):
        """Write SerialNo & Manufacturing Datecode into EEPROM of BQ2060A."""
        self.fifo_push(
            ((s.ovbatIn, 0.5), (s.sn_entry_ini, ('9136861F1234', )), ))

        m.dmm_NoFinal.measure(timeout=5)
        d.rla_vbat.set_on()
        d.dcs_vbat.output(12.20, output=True)
        d.rla_PicReset.set_on()
        time.sleep(2)
        d.rla_EVM.set_on()
        sernum = m.ui_SnEntry.measure().reading1
        sernum = sernum[-4:]    # Last 4 digits only
        current_date = datetime.date.today().isoformat()
        self._ev.sn_date(datecode=current_date, serialno=sernum)


class Final(_Main):

    """CMR-SBP Final Test Program."""

    def open(self):
        """Prepare for testing."""
        self._limits = LIMITS[self.parameter]
        super().open()
        self._isFin = True
        self.steps = (
            tester.TestStep('Startup', self._step_startup),
            tester.TestStep('Verify', self._step_verify),
            )
        global m
        m = MeasureFin(s, self._limits)

    def _step_startup(self):
        """Power comms interface, connect to PIC."""
        sernum_limit = self._limits['SerNum'].limit
        if '40214' in sernum_limit:
            sernum_push = 'G240214F1234'
        if '40166' in sernum_limit:
            sernum_push = 'G240166F1234'
        if '403' in sernum_limit:
            sernum_push = 'G240323F1234'
        self.fifo_push(((s.sn_entry_fin, (sernum_push, )), ))

        sernum = m.ui_SnEntry.measure().reading1
        self._limits['SerNumChk'].limit = str(int(sernum[-4:]))
        d.dcs_Vcom.output(12.0, output=True)
        time.sleep(1)
        d.rla_Pic.set_on()

    def _step_verify(self):
        """Read data broadcast from the PIC and verify values."""
        self.fifo_push(((s.ovbatIn, 13.72), ))

        dmm_vbatIn = m.dmm_vbatIn.measure(timeout=5).reading1
        cmr_data = self._read_data()
        s.oMirvbatIn.store(cmr_data['VOLTAGE'])
        s.oMirErrV.store(dmm_vbatIn - cmr_data['VOLTAGE'])
        s.oMirCycleCnt.store(cmr_data['CYCLE COUNT'])
        status = self.bit_status(cmr_data['BATTERY MODE'], 7)
        s.oMirRelrnFlg.store(status)
        s.oMirSw.store(cmr_data['ROTARY SWITCH READING'])
        s.oMirSenseRes.store(cmr_data['SENSE RESISTOR READING'])
        s.oMirCapacity.store(cmr_data['FULL CHARGE CAPACITY'])
        s.oMirRelStateCharge.store(cmr_data['REL STATE OF CHARGE'])
        s.oMirHalfCell.store(cmr_data['HALF CELL READING'])
        status = self.bit_status(cmr_data['PACK STATUS AND CONFIG'], 7)
        s.oMirVFCcalStatus.store(status)
        s.oMirSerNum.store(str(cmr_data['SERIAL NUMBER']))
        tester.MeasureGroup(
            (m.cmr_vbatIn, m.cmr_ErrV, m.cmr_CycleCnt, m.cmr_RelrnFlg,
             m.cmr_Sw, m.cmr_SenseRes, m.cmr_Capacity, m.cmr_RelStateCharge,
             m.cmr_Halfcell, m.cmr_VFCcalStatus, m.cmr_SerNum), )

    @staticmethod
    def bit_status(num, check_bit):
        """Check if a bit in an integer is 1 or 0.

        num - Integer.
        check_bit - Bit number to check.
        Return true if bit is set otherwise false.

        """
        mask = 1 << check_bit
        return True if num & mask else False


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
            port=CMR_PORT, baudrate=9600, timeout=0.1)
        self.cmr = cmrsbp.CmrSbp(self.cmr_ser, data_timeout=10.0)
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            PIC_HEX, folder, '18F252', self.rla_Prog)

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_vbat, self.dcs_Vchg, self.dcs_Vcom):
            dcs.output(0.0, False)
        self.dcl_ibat.output(0.0)
        for rla in (
                self.rla_vbat, self.rla_PicReset, self.rla_Prog,
                self.rla_EVM, self.rla_Pic, self.rla_Erase):
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
