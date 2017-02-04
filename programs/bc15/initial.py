#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Initial Test Program."""

import os
import inspect
import time
import tester
from tester.testlimit import (
    lim_lo, lim_hi,
    lim_hilo, lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_string)
import share
from . import console

BIN_VERSION = '1.0.13136.1528'      # Software binary version

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_BIN = 'bc15_{}.bin'.format(BIN_VERSION)

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('ACin', 240.0, 5.0),
    lim_hilo_delta('Vbus', 335.0, 10.0),
    lim_hilo_delta('14Vpri', 14.0, 1.0),
    lim_hilo('12Vs', 11.7, 13.0),
    lim_hilo_delta('5Vs', 5.0, 0.1),
    lim_hilo('3V3', 3.20, 3.35),
    lim_lo('FanOn', 0.5),
    lim_hi('FanOff', 11.0),
    lim_hilo_delta('15Vs', 15.5, 1.0),
    lim_hilo_percent('Vout', 14.40, 5.0),
    lim_hilo_percent('VoutCal', 14.40, 1.0),
    lim_lo('VoutOff', 2.0),
    lim_hilo_percent('OCP', 15.0, 5.0),
    lim_lo('InOCP', 12.0),
    lim_lo('FixtureLock', 20),
    lim_hi('FanShort', 100),
    # Data reported by the ARM
    lim_string('ARM-SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_hilo_percent('ARM-Vout', 14.40, 5.0),
    lim_hilo('ARM-2amp', 0.5, 3.5),
    # Why 'Lucky'?
    #   The circuit specs are +/- 1.5A, and we hope to be lucky
    #   and get units within +/- 1.0A ...
    lim_hilo_delta('ARM-2amp-Lucky', 2.0, 1.0),
    lim_hilo_delta('ARM-14amp', 14.0, 2.0),
    lim_hilo_int('ARM-switch', 3),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """BC15 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PartDetect', self._step_part_detect),
            tester.TestStep(
                'ProgramARM', self._step_program_arm, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('Loaded', self._step_loaded),
            )
        global d, s, m
        self._limits = LIMITS
        d = LogicalDevices(self.physical_devices, self.fifo)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)
        # Apply power to fixture Comms circuit.
        d.dcs_vcom.output(12.0, True)
        time.sleep(2)       # Allow OS to detect USB serial port

    def close(self):
        """Finished testing."""
        global m, d, s
        # Remove power from fixture circuit.
        d.dcs_vcom.output(0, False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _bc15_putstartup(self, put_defaults):
        """Push startup banner strings into fake serial port."""
        d.bc15.puts(
            'BC15\r\n'                          # BEGIN Startup messages
            'Build date:       06/11/2015\r\n'
            'Build time:       15:31:40\r\n'
            'SystemCoreClock:  48000000\r\n'
            'Software version: 1.2.3.456\r\n'
            'nonvol: reading crc invalid at sector 14 offset 0\r\n'
            'nonvol: reading nonvol2 OK at sector 15 offset 2304\r\n'
            'Hardware version: 0.0.[00]\r\n'
            'Serial number:    A9999999999\r\n'
            'Please type help command.'         # END Startup messages
            )
        if put_defaults:
            for str in (
                ('OK', ) * 3 +
                ('{}'.format(BIN_VERSION), )
                ):
                d.bc15.puts(str)

    def _step_part_detect(self):
        """Measure fixture lock and part detection microswitches."""
        self.fifo_push(((s.olock, 0.0), (s.ofanshort, 3300.0), ))

        tester.MeasureGroup((m.dmm_lock, m.dmm_fanshort, ), timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        3V3 is injected to power the ARM for programming.

        """
        self.fifo_push(((s.o3V3, 3.3), ))

        d.dcs_3v3.output(9.0, True)
        m.dmm_3V3.measure(timeout=5)
        time.sleep(2)
        d.programmer.program()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected voltage.
        Write Non-Volatile memory defaults.
        Switch off the injected voltage.

        """
        self._bc15_putstartup(True)

        d.dcs_3v3.output(9.0, True)
        d.bc15.open()
        d.rla_reset.pulse(0.1)
        time.sleep(0.5)
        d.bc15.action(None, delay=1.5, expected=10)  # Flush banner
        d.bc15['UNLOCK'] = True
        d.bc15['NVDEFAULT'] = True
        d.bc15['NVWRITE'] = True
        m.arm_SwVer.measure()
        d.bc15.close()
        d.dcs_3v3.output(0.0, False)

    def _step_powerup(self):
        """Power up the Unit.

        Power up with 240Vac.
        Go into Power Supply mode.

        """
        self.fifo_push(
            ((s.oACin, 240.0), (s.oVbus, 330.0), (s.o12Vs, 12.0),
             (s.o3V3, 3.3), (s.o15Vs, 15.0), (s.oVout, 0.2), ))
        self._bc15_putstartup(False)
        for str in (('', ) * 10):
            d.bc15.puts(str)

        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (m.dmm_acin, m.dmm_vbus, m.dmm_12Vs, m.dmm_3V3,
             m.dmm_15Vs, m.dmm_voutoff, ), timeout=5)
        d.bc15.open()
        d.bc15.action(None, delay=1.5, expected=10)  # Flush banner
        d.bc15.ps_mode()
# TODO: Save the "Power Supply" mode state in the unit (new command required)

    def _step_output(self):
        """Tests of the output.

        Check the accuracy of the current sensor.

        """
        self.fifo_push(((s.oVout, 14.40), ))
        d.bc15.puts(
            'not-pulsing-volts=14432 ;mV \r\nnot-pulsing-current=1987 ;mA ')
        d.bc15.puts('3')
        d.bc15.puts('mv-set=14400 ;mV \r\nnot-pulsing-volts=14432 ;mV ')
        d.bc15.puts(
            'set_volts_mv_num                        902 \r\n'
            'set_volts_mv_den                      14400 ')
        for str in (('', ) * 3):
            d.bc15.puts(str)

        d.dcl.output(2.0, True)
        time.sleep(0.5)
        d.bc15.stat()
        vout = tester.MeasureGroup(
            (m.dmm_vout, m.arm_vout, m.arm_2amp, m.arm_2amp_lucky,
             m.arm_switch, )).reading1
        # Calibrate output voltage
        d.bc15.cal_vout(vout)
        self.fifo_push(((s.oVout, 14.40), ))
        m.dmm_vout_cal.measure()

    def _step_loaded(self):
        """Tests of the output."""
        self.fifo_push(((s.oVout, (14.4, ) * 5 + (11.0, ), ), ))
        d.bc15.puts(
            'not-pulsing-volts=14432 ;mV \r\nnot-pulsing-current=14000 ;mA ')

        d.dcl.output(14.0, True)
        time.sleep(0.5)
        d.bc15.stat()
        tester.MeasureGroup(
            (m.dmm_vout, m.arm_vout, m.arm_14amp, m.ramp_ocp, ))


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_vcom = tester.DCSource(devices['DCS1'])
        self.dcs_3v3 = tester.DCSource(devices['DCS2'])
        self.dcs_out = tester.DCSource(devices['DCS3'])
        self.dcl = tester.DCLoad(devices['DCL1'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        self.rla_outrev = tester.Relay(devices['RLA3'])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            ARM_BIN)
        self.programmer = share.ProgramARM(
            ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the BC15 console
        bc15_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        bc15_ser.port = ARM_PORT
        # BC15 Console driver
        self.bc15 = console.Console(bc15_ser)

    def reset(self):
        """Reset instruments."""
        self.bc15.close()
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        self.dcl.output(0.0, False)
        for dcs in (self.dcs_3v3, self.dcs_out):
            dcs.output(0.0, output=False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_outrev):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        bc15 = logical_devices.bc15
        sensor = tester.sensor
        self.olock = sensor.Res(dmm, high=12, low=5, rng=10000, res=1)
        self.ofanshort = sensor.Res(dmm, high=13, low=6, rng=10000, res=1)
        self.oACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.o14Vpri = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self.o12Vs = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o5Vs = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.ofan = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.o15Vs = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oVout = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=14.0, stop=17.0, step=0.25, delay=0.1)
        self.arm_swver = console.Sensor(
            bc15, 'SW_VER', rdgtype=sensor.ReadingString)
        self.arm_vout = console.Sensor(
            bc15, 'not-pulsing-volts', scale=0.001)
        self.arm_iout = console.Sensor(
            bc15, 'not-pulsing-current', scale=0.001)
        self.arm_switch = console.Sensor(bc15, 'SWITCH')


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_fanshort = Measurement(limits['FanShort'], sense.ofanshort)
        self.dmm_acin = Measurement(limits['ACin'], sense.oACin)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.oVbus)
        self.dmm_14Vpri = Measurement(limits['14Vpri'], sense.o14Vpri)
        self.dmm_12Vs = Measurement(limits['12Vs'], sense.o12Vs)
        self.dmm_5Vs = Measurement(limits['5Vs'], sense.o5Vs)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_fanon = Measurement(limits['FanOn'], sense.ofan)
        self.dmm_fanoff = Measurement(limits['FanOff'], sense.ofan)
        self.dmm_15Vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_vout_cal = Measurement(limits['VoutCal'], sense.oVout)
        self.dmm_voutoff = Measurement(limits['VoutOff'], sense.oVout)
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
        self.arm_SwVer = Measurement(limits['ARM-SwVer'], sense.arm_swver)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.arm_vout)
        self.arm_2amp = Measurement(limits['ARM-2amp'], sense.arm_iout)
        self.arm_2amp_lucky = Measurement(
            limits['ARM-2amp-Lucky'], sense.arm_iout)
        self.arm_switch = Measurement(limits['ARM-switch'], sense.arm_switch)
        self.arm_14amp = Measurement(limits['ARM-14amp'], sense.arm_iout)
