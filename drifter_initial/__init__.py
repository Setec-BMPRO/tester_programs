#!/usr/bin/env python3
"""Drifter Initial Test Program."""

import os
import logging
import time

import tester
from . import support
from . import limit

import share.programmer
from . import pic_driver

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA
LIMIT_DATA_BM = limit.DATA_BM

# Serial port for the PIC.
_PIC_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'\\.\COM1',
             }[os.name]

_HEX_DIR = {'posix': '/opt/setec/ate4/drifter_initial',
            'nt': r'C:\TestGear\Python\TcpServer\drifter_initial',
            }[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Drifter Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, True),
            ('CalPre', self._step_cal_pre, None, True),
            ('CalVolts', self._step_cal_volts, None, True),
            ('CalCurrent', self._step_cal_curr, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._picdev = pic_driver.Console(port=_PIC_PORT)
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits, self._picdev)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._picdev.close()
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input DC and measure voltages."""
        self.fifo_push(((s.oVin, 12.0), (s.oVcc, 3.3), ))

        t.pwr_up.run()

    def _step_program(self):
        """Program the PIC device."""
        self._logger.info('Start PIC programmer')
        d.rla_Prog.set_on()
        hexfile = self._limits['Software'].limit
        self._logger.debug('HexFile "%s"', hexfile)
        pic = share.programmer.ProgramPIC(hexfile=hexfile,
                                          working_dir=_HEX_DIR,
                                          device_type='18F87J93',
                                          sensor=s.oMirPIC,
                                          fifo=self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        m.pgmPIC.measure()

    def _step_cal_pre(self):
        """
        Setup the PIC device for calibration.

        The PIC is accessed via the serial port.

        """
        self.fifo_push(
            ((s.oPic_Status, 0), (s.oVsw, 3.3), (s.oVref, 3.3),
             (s.o3V3, -2.7), (s.o0V8, -0.8), ))
        d.dcs_RS232.output(10.0, True)
        time.sleep(4)
        if not self._fifo:
            self._picdev.open()
        self._picdev.defaults()
        m.pic_Status.measure(timeout=5)
        self._picdev.aps_disable()
        MeasureGroup(
            (m.dmm_Vsw, m.dmm_Vref, m.dmm_3V3, m.dmm_0V8, ), timeout=5)

    def _step_cal_volts(self):
        """Calibrate battery voltage."""
        self.fifo_push(
            ((s.oVin, 12.0), (s.oPic_ZeroChk, -35), (s.oPic_Status, 0),
             (s.oPic_Vin, (11.95, 11.98)), ))
        d.rla_ZeroCal.set_on()
        time.sleep(2)
        self._picdev.cal_reload()
        m.pic_ZeroChk.measure(timeout=5)
        self._picdev.cal_zero_curr()
        self._picdev.offset()
        dmm_vin = m.dmm_vin.measure(timeout=5)[1][0]
        pic_vin = m.pic_vin.measure(timeout=5)[1][0]
        err = ((dmm_vin - pic_vin) / dmm_vin) * 100
        s.oMirErrorV.store(err)
        m.ErrorV.measure()
        # Calibrate voltage if required
        if err != self._limits['%CalV']:
            self._picdev.cal_volts(dmm_vin)
            m.pic_Status.measure(timeout=5)
            self._picdev.cal_reload()
            pic_vin = m.pic_vin.measure(timeout=5)[1][0]
            err = ((dmm_vin - pic_vin) / dmm_vin) * 100
            s.oMirErrorV.store(err)
            m.CalV.measure()
        d.rla_ZeroCal.set_off()

    def _step_cal_curr(self):
        """Calibrate battery current."""
        self.fifo_push(((s.opic_isense, (-89.0, -89.9)), (s.oIsense, 0.090),
                         (s.oPic_Status, 0), (s.oVin, 12.0), (s.oVcc, 3.3),
                         (s.oPic_Vfactor, 20000), (s.oPic_Ifactor, 15000),
                         (s.oPic_Ioffset, -8), (s.oPic_Ithreshold, 160), ))
        d.dcs_SlopeCal.output(17.1, True)
        time.sleep(2)
        self._picdev.cal_reload()
        dmm_isense = m.dmm_isense.measure(timeout=5)[1][0]
        time.sleep(0.1)
        pic_isense = m.pic_isense.measure(timeout=5)[1][0]
        err = ((dmm_isense - pic_isense) / dmm_isense) * 100
        s.oMirErrorI.store(err)
        m.ErrorI.measure()
        # Calibrate current if required
        if err != self._limits['%CalI']:
            self._picdev.cal_curr(dmm_isense)
            m.pic_Status.measure(timeout=5)
            self._picdev.cal_reload()
            pic_isense = m.pic_isense.measure(timeout=5)[1][0]
            err = ((dmm_isense - pic_isense) / dmm_isense) * 100
            s.oMirErrorI.store(err)
            m.CalI.measure()
        d.dcs_SlopeCal.output(0.0, False)
        t.reset.run()
        self._picdev.unlock()
        m.pic_Vfactor.measure(timeout=5)
        m.pic_Ifactor.measure(timeout=5)
        m.pic_Ioffset.measure(timeout=5)
        m.pic_Ithreshold.measure(timeout=5)
