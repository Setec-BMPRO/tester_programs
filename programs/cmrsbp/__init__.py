#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMR-SBP ALL Test Program."""

import os
import inspect
import logging
import datetime
import threading
import time
import tester
from . import support
from . import limit
from . import cmrsbp
from . import ev2200
from share.programmer import ProgramPIC
from share.sim_serial import SimSerial

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA             # CMR-SBP Initial and SerDate limits
LIMIT_DATA_8D = limit.DATA_8D       # CMR-SBP-8-D-NiMH Final limits
LIMIT_DATA_13F = limit.DATA_13F     # CMR-SBP-13-F-NiMH Final limits
LIMIT_DATA_17L = limit.DATA_17L     # CMR-SBP-17-LiFePO4 Final limits


_PIC_HEX = 'CMR-SBP-9.hex'

# Serial port for the EV2200.
_EV_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Serial port for the CMR.
_CMR_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM2'}[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


def _bit_status(num, check_bit):
    """Check if a binary bit in an integer is 1 or 0.

    num - Integer.
    check_bit - Binary bit number to check.
    Return true if bit is set otherwise false.

    """
    mask = 1 << check_bit
    result = True if num & mask else False
#    print('Bit %s of integer %s (binary %s) = %s',
#        check_bit, num, bin(65536 + num), result)
    return result


class _Main(tester.TestSequence):

    """CMR-SBP Base Test Program."""

    def __init__(self, selection, sequence, fifo):
        """Common test program segments.

           @param selection Product test program
           @param sequence Test sequence
           @param fifo True to enable FIFOs

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._isFin = False
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        self._logger.info('BaseOpen')
        self._cmr_ser = SimSerial(
            simulation=self._fifo,
            port=_CMR_PORT, baudrate=9600, timeout=0.1)
        self._cmr = cmrsbp.CmrSbp(self._cmr_ser, data_timeout=10.0)
        global d, s
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('BaseClose')
        self._cmr.close()
        self._cmr_ser.close()
        global m, d, s, t
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _read_data(self):
        """Read data broadcast from PIC.

        @return Dictionary of CMR data.

        """
        if self._fifo:
            _str = """
#BATTERY MODE,24576
#TEMPERATURE,297.0
#VOLTAGE,13.710
#CURRENT,0.0
#REL STATE OF CHARGE,100
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
#SERIAL NUMBER,0778
"""
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
                    sense_res = 450
                    full_charge = 17000
            data_str = _str.format(full_charge, half_cell, sense_res)
            def myputs():   # This will push the later when timer is done
                self._cmr_ser.puts(data_str)
            tmr = threading.Timer(0.5, myputs)
            tmr.start()     # Push data once we are inside _cmr.read()
        data = self._cmr.read()
        self._logger.debug('Received data: %s', data)
        return data


class MainInitial(_Main):

    """CMR-SBP Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True to enable FIFOs

        """
        self._devices = physical_devices
        self._limits = test_limits
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, True),
            ('CheckPicValues', self._step_check_pic_vals, None, True),
            ('CheckVcharge', self._step_check_vchge, None, True),
            ('CalBQvolts', self._step_calv, None, True),
            ('CalBQcurrent', self._step_cali, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        self._ev_ser = SimSerial(
            simulation=self._fifo,
            port=_EV_PORT, baudrate=9600, timeout=4.0)
        self._ev = ev2200.EV2200(self._ev_ser)
        global m, t
        m = support.MeasureInit(s, self._limits)
        t = support.SubTestInit(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._ev_ser.close()
        super().close()

    def _step_power_up(self):
        """Power up with vbat.

           Check that a Final Unit is not connected.
           Apply vbat and measure voltages.

        """
        self.fifo_push(((s.ovbatIn, 0.5), (s.ovbat, 12.0), (s.oVcc, 3.3), ))

        t.pwrup.run()

    def _step_program(self):
        """Program the PIC micro.

           Apply 5.0V to Vdd.
           Program.

        """
        self.fifo_push(((s.oVcc, 5.0), ))

        d.rla_Erase.set_on()
        m.dmm_VErase.measure(timeout=5)
        self._logger.info('Start PIC programmer')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        d.rla_Prog.set_on()
        pic = ProgramPIC(
            hexfile=_PIC_HEX, working_dir=folder,
            device_type='18F252', sensor=s.oMirPIC,
            fifo=self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        d.rla_Erase.set_off()
        m.pgmPIC.measure()

    def _step_check_pic_vals(self):
        """Check some values from the PIC.

           Power Comms interface and connect to PIC.
           Read PIC and check values.

        """
        t.pwr_comms.run()
        cmr_data = self._read_data()
        s.oMirSenseRes.store(cmr_data['SENSE RESISTOR READING'])
        s.oMirHalfCell.store(cmr_data['HALF CELL READING'])
        s.oMirVChge.store(cmr_data['CHARGE INPUT READING'])
        tester.measure.group((m.cmr_SenseRes, m.cmr_Halfcell, m.cmr_VChgeOn),)

    def _step_check_vchge(self):
        """Check Vcharge."""
        self.fifo_push(((s.ovbat, 12.0), (s.oVcc, 3.3), ))

        t.chk_vch.run()

    def _step_calv(self):
        """Calibrate vbat for BQ2060A."""
        self.fifo_push(((s.ovbat, 12.0), ))

        t.cal_setup.run()
        dmm_vbat = m.dmm_vbat.measure(timeout=5)[1][0]
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
        dmm_ibat = m.dmm_ibat.measure(timeout=5)[1][0]
        time.sleep(3.0)
        ev_data = self._ev.read_vit()
        s.oMirErrI.store(dmm_ibat - ev_data['Current'])
        m.bq_ErrIUncal.measure()
        self._ev.cal_i(dmm_ibat)
        ev_data = self._ev.read_vit()
        s.oMirErrI.store(dmm_ibat - ev_data['Current'])
        m.bq_ErrICal.measure()
        d.dcl_ibat.output(0.0)


class MainSerialDate(_Main):

    """CMR-SBP SerialDate Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True to enable FIFOs

        """
        self._devices = physical_devices
        self._limits = test_limits
        sequence = (
            ('SerialDate', self._step_sn_date, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        self._ev_ser = SimSerial(
            simulation=self._fifo,
            port=_EV_PORT, baudrate=9600, timeout=4.0)
        self._ev = ev2200.EV2200(self._ev_ser)
        global m
        m = support.MeasureInit(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._ev_ser.close()
        super().close()

    def _step_sn_date(self):
        """Write SerialNo & Manufacturing Datecode into EEPROM of BQ2060A."""
        self.fifo_push(((s.ovbatIn, 0.5), (s.oSnEntry, ('11', )), ))

        m.dmm_NoFinal.measure(timeout=5)
        d.rla_vbat.set_on()
        d.dcs_vbat.output(12.20, output=True)
        d.rla_PicReset.set_on()
        time.sleep(2)
        d.rla_EVM.set_on()
        result, sernum = m.ui_SnEntry.measure()
        current_date = datetime.date.today().isoformat()
        self._ev.sn_date(datecode=current_date, serialno=sernum[0])


class MainFinal(_Main):

    """CMR-SBP Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True to enable FIFOs

        """
        self._devices = physical_devices
        self._limits = test_limits
        sequence = (
            ('Startup', self._step_startup, None, True),
            ('Verify', self._step_verify, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._isFin = True

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        global m
        m = support.MeasureFin(s, self._limits)

    def _step_startup(self):
        """Power comms interface, connect to PIC."""
        self.fifo_push(((s.oSnEntry, ('G240166F0778', )), ))

        result, (sernum, ) = m.ui_SnEntry.measure()
        self._limits['SerNum'].limit = str(int(sernum[-4:]))
        d.dcs_Vcom.output(12.0, output=True)
        time.sleep(1)
        d.rla_Pic.set_on()

    def _step_verify(self):
        """Read data broadcast from the PIC and verify values."""
        self.fifo_push(((s.ovbatIn, 13.72), ))

        dmm_vbatIn = m.dmm_vbatIn.measure(timeout=5)[1][0]
        cmr_data = self._read_data()
        s.oMirvbatIn.store(cmr_data['VOLTAGE'])
        s.oMirErrV.store(dmm_vbatIn - cmr_data['VOLTAGE'])
        s.oMirCycleCnt.store(cmr_data['CYCLE COUNT'])
        status = _bit_status(cmr_data['BATTERY MODE'], 7)
        s.oMirRelrnFlg.store(status)
        s.oMirSw.store(cmr_data['ROTARY SWITCH READING'])
        s.oMirSenseRes.store(cmr_data['SENSE RESISTOR READING'])
        s.oMirCapacity.store(cmr_data['FULL CHARGE CAPACITY'])
        s.oMirRelStateCharge.store(cmr_data['REL STATE OF CHARGE'])
        s.oMirHalfCell.store(cmr_data['HALF CELL READING'])
        status = _bit_status(cmr_data['PACK STATUS AND CONFIG'], 7)
        s.oMirVFCcalStatus.store(status)
        s.oMirSerNum.store(str(cmr_data['SERIAL NUMBER']))
        MeasureGroup(
            (m.cmr_vbatIn, m.cmr_ErrV, m.cmr_CycleCnt, m.cmr_RelrnFlg,
             m.cmr_Sw, m.cmr_SenseRes, m.cmr_Capacity, m.cmr_RelStateCharge,
             m.cmr_Halfcell, m.cmr_VFCcalStatus, m.cmr_SerNum), )
