#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMR-SBP ALL Test Program."""

import os
import datetime
import time
import inspect
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitBetween, LimitDelta, LimitBoolean, LimitRegExp, LimitInteger
    )
import share
from . import ev2200
from . import cmrsbp


class Initial(share.TestSequence):

    """CMR-SBP Initial Test Program."""

    # PIC firmware image file
    pic_hex = 'CMR-SBP-9.hex'
    # Serial port for the EV2200.
    ev_port = share.port('017789', 'EV')
    # Serial port for the CMR.
    cmr_port = share.port('017789', 'CMR')
    # Test limits
    limitdata = (
        LimitDelta('Vbat', 12.0, 0.10),
        LimitBetween('VbatCharge', 11.8, 12.5),
        LimitDelta('Vcc', 3.3, 0.2),
        LimitBetween('VErase', 4.8, 5.05),
        LimitLow('IStart', 0.02),
        LimitBetween('Vchge', 12.8, 15.0),
        # 2.0A +/- 10mA
        LimitDelta('Ibat', -2.00, 0.01),
        LimitLow('Final Not Connected', 1.0),
        LimitDelta('SenseRes', 250, 30),
        LimitDelta('Halfcell', 110, 10),
        LimitDelta('VChgeOn', 350, 50),
        LimitDelta('ErrVUncal', 0.0, 0.5),
        LimitDelta('ErrVCal', 0.0, 0.03),
        LimitDelta('ErrIUncal', 0.0, 0.060),
        LimitDelta('ErrICal', 0.0, 0.015),
        # 298K nominal +/- 2.5K in Kelvin (25C +/- 2.5C in Celsius).
        LimitDelta('BQ-Temp', 300, 4.5),
        # SerialDate
        LimitRegExp('CmrSerNum', r'^[9A-HJ-NP-V][1-9A-C][0-9]{5}F[0-9]{4}$'),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, MeasureIni)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('Program', self._step_program),
            TestStep('CheckPicValues', self._step_check_pic_vals),
            TestStep('CheckVcharge', self._step_check_vchge),
            TestStep('CalBQvolts', self._step_calv),
            TestStep('CalBQcurrent', self._step_cali),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up with vbat.

           Check that a Final Unit is not connected.
           Apply vbat and measure voltages.

        """
        mes['dmm_NoFinal'](timeout=5)
        dev['rla_vbat'].set_on()
        dev['dcs_vbat'].output(12.20, output=True)
        self.measure(('dmm_vbat', 'dmm_Vcc', ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the PIC micro."""
        dev['rla_Erase'].set_on()
        mes['dmm_VErase'](timeout=5)
        dev['program_pic'].program()
        dev['rla_Erase'].set_off()

    @share.teststep
    def _step_check_pic_vals(self, dev, mes):
        """Check some values from the PIC.

           Power Comms interface and connect to PIC.
           Read PIC and check values.

        """
        dev['dcs_Vcom'].output(12.0, output=True)
        dev['dcs_Vchg'].output(12.6, output=True, delay=15)
        dev['rla_Pic'].set_on(delay=2)
        cmr_data = dev['cmr'].read()
        mes['cmr_SenseRes'].sensor.store(cmr_data['SENSE RESISTOR READING'])
        mes['cmr_Halfcell'].sensor.store(cmr_data['HALF CELL READING'])
        mes['cmr_VChgeOn'].sensor.store(cmr_data['CHARGE INPUT READING'])
        self.measure(('cmr_SenseRes', 'cmr_Halfcell', 'cmr_VChgeOn'), )

    @share.teststep
    def _step_check_vchge(self, dev, mes):
        """Check Vcharge."""
        dev['dcs_vbat'].output(0.0)
        dev['rla_vbat'].set_off()
        self.measure(('dmm_vbatChge', 'dmm_Vcc'), timeout=5)
        dev['rla_vbat'].set_on()

    @share.teststep
    def _step_calv(self, dev, mes):
        """Calibrate vbat for BQ2060A."""
        evdev = dev['ev']
        evdev.open()
        dev['dcs_vbat'].output(12.20)
        dev['dcs_Vchg'].output(0.0)
        dev['rla_Pic'].set_off()
        dev['rla_PicReset'].set_on(delay=2)
        dev['rla_EVM'].set_on()
        dmm_vbat = mes['dmm_vbat'](timeout=5).reading1
        ev_data = evdev.read_vit()
        mes['bq_ErrVUncal'].sensor.store(dmm_vbat - ev_data['Voltage'])
        mes['bq_Temp'].sensor.store(ev_data['Temperature'])
        self.measure(('bq_ErrVUncal', 'bq_Temp'))
        evdev.cal_v(dmm_vbat)
        ev_data = evdev.read_vit()
        mes['bq_ErrVCal'].sensor.store(dmm_vbat - ev_data['Voltage'])
        mes['bq_ErrVCal']()

    @share.teststep
    def _step_cali(self, dev, mes):
        """Calibrate ibat for BQ2060A."""
        evdev = dev['ev']
        dev['dcl_ibat'].output(2.0, True)
        dmm_ibat = mes['dmm_ibat'](timeout=5).reading1
        time.sleep(3)
        ev_data = evdev.read_vit()
        mes['bq_ErrIUncal'].sensor.store(dmm_ibat - ev_data['Current'])
        mes['bq_ErrIUncal']()
        evdev.cal_i(dmm_ibat)
        ev_data = evdev.read_vit()
        mes['bq_ErrICal'].sensor.store(dmm_ibat - ev_data['Current'])
        mes['bq_ErrICal']()
        dev['dcl_ibat'].output(0.0)


class SerialDate(share.TestSequence):

    """CMR-SBP SerialDate Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(Initial.limitdata, Devices, Sensors, MeasureIni)
        self.steps = (
            TestStep('SerialDate', self._step_sn_date),
            )

    @share.teststep
    def _step_sn_date(self, dev, mes):
        """Write SerialNo & Manufacturing Datecode into EEPROM of BQ2060A."""
        evdev = dev['ev']
        evdev.open()
        mes['dmm_NoFinal'](timeout=5)
        dev['rla_vbat'].set_on()
        dev['dcs_vbat'].output(12.20, output=True)
        dev['rla_PicReset'].set_on(delay=2)
        dev['rla_EVM'].set_on()
        sernum = mes['ui_SnEntry']().reading1[-4:]  # Last 4 digits only
        current_date = datetime.date.today().isoformat()
        evdev.sn_date(datecode=current_date, serialno=sernum)


class Final(share.TestSequence):

    """CMR-SBP Final Test Program."""

    # Common test limits
    _common = (
        LimitDelta('ErrV', 0.0, 0.03),
        LimitBetween('CycleCnt', 0.5, 20.5),
        LimitBoolean('RelrnFlg', False),
        LimitInteger('RotarySw', 256),
        LimitDelta('Halfcell', 400, 50),
        LimitBoolean('VFCcalStatus', True),
        LimitRegExp('SerNumChk', ''),
        )
    # Test limit selection keyed by program parameter
    limitdata = {
        '8': _common + (
            LimitBetween('VbatIn', 12.8, 15.0),
            LimitBetween('SenseRes', 39.0, 91.0),
            LimitBetween('Capacity', 6400, 11000),
            LimitDelta('StateOfCharge', 100.0, 10.5),
            LimitRegExp(
                'CmrSerNum', r'^[9A-HJ-NP-V][1-9A-C](36861|40214)F[0-9]{4}$'),
            ),
        '13': _common + (
            LimitBetween('VbatIn', 12.8, 15.0),
            LimitBetween('SenseRes', 221.0, 280.0),
            LimitBetween('Capacity', 11000, 15000),
            LimitDelta('StateOfCharge', 100.0, 10.5),
            LimitRegExp(
                'CmrSerNum', r'^[9A-HJ-NP-V][1-9A-C](36862|40166)F[0-9]{4}$'),
            ),
        '17': _common + (
            LimitBetween('VbatIn', 11.8, 15.0),     # Due to <30% charge
            LimitBetween('SenseRes', 400.0, 460.0),
            LimitBetween('Capacity', 15500, 20000),
            LimitLow('StateOfCharge', 30.0),
            LimitRegExp(
                'CmrSerNum', r'^[9A-HJ-NP-V][1-9A-C]403(15|23)F[0-9]{4}$'),
            ),
        }

    def open(self):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter],
            Devices, Sensors, MeasureFin)
        self.steps = (
            TestStep('Startup', self._step_startup),
            TestStep('Verify', self._step_verify),
            )

    @share.teststep
    def _step_startup(self, dev, mes):
        """Power comms interface, connect to PIC."""
        sernum = mes['ui_SnEntry']().reading1
        self.limits['SerNumChk'].limit = str(int(sernum[-4:]))
        dev['dcs_Vcom'].output(12.0, output=True, delay=1)
        dev['rla_Pic'].set_on()

    @share.teststep
    def _step_verify(self, dev, mes):
        """Read data broadcast from the PIC and verify values."""
        dmm_vbatIn = mes['dmm_vbatIn'](timeout=5).reading1
        cmr_data = dev['cmr'].read()
        mes['cmr_vbatIn'].sensor.store(cmr_data['VOLTAGE'])
        mes['cmr_ErrV'].sensor.store(dmm_vbatIn - cmr_data['VOLTAGE'])
        mes['cmr_CycleCnt'].sensor.store(cmr_data['CYCLE COUNT'])
        status = self.bit_status(cmr_data['BATTERY MODE'], 7)
        mes['cmr_RelrnFlg'].sensor.store(status)
        mes['cmr_Sw'].sensor.store(cmr_data['ROTARY SWITCH READING'])
        mes['cmr_SenseRes'].sensor.store(cmr_data['SENSE RESISTOR READING'])
        mes['cmr_Capacity'].sensor.store(cmr_data['FULL CHARGE CAPACITY'])
        mes['cmr_RelStateCharge'].sensor.store(cmr_data['REL STATE OF CHARGE'])
        mes['cmr_Halfcell'].sensor.store(cmr_data['HALF CELL READING'])
        status = self.bit_status(cmr_data['PACK STATUS AND CONFIG'], 7)
        mes['cmr_VFCcalStatus'].sensor.store(status)
        mes['cmr_SerNum'].sensor.store(str(cmr_data['SERIAL NUMBER']))
        self.measure(
            ('cmr_vbatIn', 'cmr_ErrV', 'cmr_CycleCnt', 'cmr_RelrnFlg',
             'cmr_Sw', 'cmr_SenseRes', 'cmr_Capacity', 'cmr_RelStateCharge',
             'cmr_Halfcell', 'cmr_VFCcalStatus', 'cmr_SerNum'), )

    @staticmethod
    def bit_status(num, check_bit):
        """Check if a bit in an integer is 1 or 0.

        num - Integer.
        check_bit - Bit number to check.
        Return true if bit is set otherwise false.

        """
        mask = 1 << check_bit
        return True if num & mask else False


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_Vchg', tester.DCSource, 'DCS1'),
                ('dcs_Vcom', tester.DCSource, 'DCS2'),
                ('dcl_ibat', tester.DCLoad, 'DCL1'),
                ('rla_vbat', tester.Relay, 'RLA5'),
                ('rla_PicReset', tester.Relay, 'RLA6'),
                ('rla_Prog', tester.Relay, 'RLA7'),
                ('rla_EVM', tester.Relay, 'RLA8'),  # Enables the EV2200
                ('rla_Pic', tester.Relay, 'RLA9'),  # Connect to PIC
                # Apply 5V to Vdd for Erasing PIC
                ('rla_Erase', tester.Relay, 'RLA10'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcs_vbat'] = tester.DCSourceParallel(
            (tester.DCSource(self.physical_devices['DCS3']),
             tester.DCSource(self.physical_devices['DCS4']),
             tester.DCSource(self.physical_devices['DCS5']),
            ))
        # Open serial connection to data monitor
        cmr_ser = serial.Serial(
            port=Initial.cmr_port, baudrate=9600, timeout=0.1)
        self['cmr'] = cmrsbp.CmrSbp(cmr_ser, data_timeout=10)
        self.add_closer(self['cmr'].close)
        # EV2200 board
        ev_ser = serial.Serial(baudrate=9600, timeout=4)
        # Set port separately, as we don't want it opened yet
        ev_ser.port = Initial.ev_port
        self['ev'] = ev2200.EV2200(ev_ser)
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_pic'] = share.ProgramPIC(
            Initial.pic_hex, folder, '18F252', self['rla_Prog'])

    def reset(self):
        """Reset instruments."""
        self['ev'].close()
        for dcs in ('dcs_vbat', 'dcs_Vchg', 'dcs_Vcom'):
            self[dcs].output(0.0, False)
        self['dcl_ibat'].output(0.0)
        for rla in (
                'rla_vbat', 'rla_PicReset', 'rla_Prog',
                'rla_EVM', 'rla_Pic', 'rla_Erase'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oMirvbatIn'] = sensor.Mirror()
        self['oMirCycleCnt'] = sensor.Mirror()
        self['oMirRelrnFlg'] = sensor.Mirror()
        self['oMirSenseRes'] = sensor.Mirror()
        self['oMirCapacity'] = sensor.Mirror()
        self['oMirRelStateCharge'] = sensor.Mirror()
        self['oMirHalfCell'] = sensor.Mirror()
        self['oMirVFCcalStatus'] = sensor.Mirror()
        self['oMirVChge'] = sensor.Mirror()
        self['oMirErrV'] = sensor.Mirror()
        self['oMirErrI'] = sensor.Mirror()
        self['oMirTemp'] = sensor.Mirror()
        self['oMirSw'] = sensor.Mirror()
        self['oMirSerNum'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['ovbatIn'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['ovbat'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.0001)
        self['oVcc'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self['oVchge'] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self['oibat'] = sensor.Vdc(
            dmm, high=4, low=2, rng=0.1, res=0.000001, scale=100.0)
        self['sn_entry_ini'] = sensor.DataEntry(
            message=tester.translate('cmrsbp_sn', 'msgSnEntryIni'),
            caption=tester.translate('cmrsbp_sn', 'capSnEntry'))
        self['sn_entry_fin'] = sensor.DataEntry(
            message=tester.translate('cmrsbp_sn', 'msgSnEntryFin'),
            caption=tester.translate('cmrsbp_sn', 'capSnEntry'))


class MeasureIni(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('cmr_SenseRes', 'SenseRes', 'oMirSenseRes', ''),
            ('cmr_Halfcell', 'Halfcell', 'oMirHalfCell', ''),
            ('cmr_VChgeOn', 'VChgeOn', 'oMirVChge', ''),
            ('bq_ErrVUncal', 'ErrVUncal', 'oMirErrV', ''),
            ('bq_ErrIUncal', 'ErrIUncal', 'oMirErrI', ''),
            ('bq_Temp', 'BQ-Temp', 'oMirTemp', ''),
            ('bq_ErrVCal', 'ErrVCal', 'oMirErrV', ''),
            ('bq_ErrICal', 'ErrICal', 'oMirErrI', ''),
            ('dmm_NoFinal', 'Final Not Connected', 'ovbatIn', ''),
            ('dmm_vbat', 'Vbat', 'ovbat', ''),
            ('dmm_vbatChge', 'VbatCharge', 'ovbat', ''),
            ('dmm_Vcc', 'Vcc', 'oVcc', ''),
            ('dmm_VErase', 'VErase', 'oVcc', ''),
            ('dmm_Vchge', 'Vchge', 'oVchge', ''),
            ('dmm_ibat', 'Ibat', 'oibat', ''),
            ('ui_SnEntry', 'CmrSerNum', 'sn_entry_ini', ''),
            ))


class MeasureFin(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('ui_SnEntry', 'CmrSerNum', 'sn_entry_fin', ''),
            ('dmm_vbatIn', 'VbatIn', 'ovbatIn', ''),
            ('cmr_vbatIn', 'VbatIn', 'oMirvbatIn', ''),
            ('cmr_ErrV', 'ErrV', 'oMirErrV', ''),
            ('cmr_CycleCnt', 'CycleCnt', 'oMirCycleCnt', ''),
            ('cmr_RelrnFlg', 'RelrnFlg', 'oMirRelrnFlg', ''),
            ('cmr_Sw', 'RotarySw', 'oMirSw', ''),
            ('cmr_SenseRes', 'SenseRes', 'oMirSenseRes', ''),
            ('cmr_Capacity', 'Capacity', 'oMirCapacity', ''),
            ('cmr_RelStateCharge', 'StateOfCharge', 'oMirRelStateCharge', ''),
            ('cmr_Halfcell', 'Halfcell', 'oMirHalfCell', ''),
            ('cmr_VFCcalStatus', 'VFCcalStatus', 'oMirVFCcalStatus', ''),
            ('cmr_SerNum', 'SerNumChk', 'oMirSerNum', ''),
            ))
