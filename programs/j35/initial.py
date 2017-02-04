#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""J35 Initial Test Program."""

import os
import inspect
import time
from pydispatch import dispatcher
import tester
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_lo, lim_boolean, lim_string,
    lim_hilo_int, lim_hilo_percent
    )
import share
from share import oldteststep
from . import console

ARM_VERSION = '1.1.14080.920'      # ARM versions
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_BIN = 'j35_{}.bin'.format(ARM_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,36,0'
# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28
COUNT_A = 7
CURRENT_A = 14.0
COUNT_BC = 14
CURRENT_BC = 28.0

_COMMON = (
    lim_hilo_delta('ACin', 240.0, 5.0),
    lim_hilo('Vbus', 335.0, 345.0),
    lim_hilo('12Vpri', 11.5, 13.0),
    lim_hilo('Vload', 12.0, 12.9),
    lim_lo('VloadOff', 0.5),
    lim_hilo_delta('VbatIn', 12.0, 0.5),
    lim_hilo_delta('VbatOut', 13.5, 0.5),
    lim_hilo_delta('Vbat', 12.8, 0.2),
    lim_hilo_percent('VbatLoad', 12.8, 5),
    lim_hilo_delta('Vaux', 13.5, 0.5),
    lim_hilo_delta('Vair', 13.5, 0.5),
    lim_hilo_delta('3V3U', 3.30, 0.05),
    lim_hilo_delta('3V3', 3.30, 0.05),
    lim_hilo('15Vs', 11.5, 13.0),
    lim_hilo_delta('FanOn', 12.5, 0.5),
    lim_lo('FanOff', 0.5),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('ARM-SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_hilo_delta('ARM-AuxV', 13.5, 0.37),
    lim_hilo('ARM-AuxI', 0.0, 1.5),
    lim_hilo_int('Vout_OV', 0),     # Over-voltage not triggered
    lim_hilo_delta('ARM-AcV', 240.0, 10.0),
    lim_hilo_delta('ARM-AcF', 50.0, 3.0),
    lim_hilo('ARM-SecT', 8.0, 70.0),
    lim_hilo_delta('ARM-Vout', 12.8, 0.356),
    lim_hilo('ARM-Fan', 0, 100),
    lim_hilo_delta('ARM-BattI', 4.0, 1.0),
    lim_hilo_delta('ARM-LoadI', 2.1, 0.9),
    lim_hilo_delta('CanPwr', 12.0, 1.0),
    lim_string('CAN_RX', r'^RRQ,36,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_lo('InOCP', 11.6),
    lim_lo('FixtureLock', 20),
    lim_boolean('Notify', True),
    )

LIMITS_A = tester.testlimit.limitset(_COMMON + (
    lim_string('Variant', 'J35A'),
    lim_lo('LOAD_COUNT', COUNT_A),
    lim_lo('LOAD_CURRENT', CURRENT_A),
    lim_hilo('OCP', 20.0 - CURRENT_A, 25.0 - CURRENT_A),
    ))

LIMITS_B = tester.testlimit.limitset(_COMMON + (
    lim_string('Variant', 'J35B'),
    lim_lo('LOAD_COUNT', COUNT_BC),
    lim_lo('LOAD_CURRENT', CURRENT_BC),
    lim_hilo('OCP', 35.0 - CURRENT_BC, 42.0 - CURRENT_BC),
    ))

LIMITS_C = tester.testlimit.limitset(_COMMON + (
    lim_string('Variant', 'J35C'),
    lim_lo('LOAD_COUNT', COUNT_BC),
    lim_lo('LOAD_CURRENT', CURRENT_BC),
    lim_hilo('OCP', 35.0 - CURRENT_BC, 42.0 - CURRENT_BC),
    ))

LIMITS = {      # Test limit selection keyed by program parameter
    'A': LIMITS_A,
    'B': LIMITS_B,
    'C': LIMITS_C,
    }

# Variant specific data. Indexed by open() parameter.
#   'HwVer': Hardware version data.
#   'SolarCan': Enable Solar input & CAN bus tests.
#   'Derate': Derate output current.
VARIANT = {
    'A': {
        'HwVer': (2, 1, 'A'),
        'SolarCan': False,
        'Derate': True,
        },
    'B': {
        'HwVer': (2, 2, 'A'),
        'SolarCan': False,
        'Derate': False,
        },
    'C': {
        'HwVer': (6, 3, 'A'),
        'SolarCan': True,
        'Derate': False,
        },
    }


class Initial(tester.TestSequence):     # pylint:disable=R0902

    """J35 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        if self.parameter is None:
            self.parameter = 'C'
        self.limits = LIMITS[self.parameter]
        self.variant = VARIANT[self.parameter]
        self.logdev = LogicalDevices(self.physical_devices, self.fifo)
        self.sensors = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensors, self.limits)
        self.steps = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep(
                'ProgramARM', self._step_program_arm, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('Aux', self._step_aux),
            tester.TestStep(
                'Solar', self._step_solar, self.variant['SolarCan']),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            tester.TestStep('Load', self._step_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep(
                'CanBus', self._step_canbus, self.variant['SolarCan']),
            )
        # Power to fixture Comms circuits.
        self.logdev.dcs_vcom.output(9.0, True)

    def close(self):
        """Finished testing."""
        self.logdev.dcs_vcom.output(0, False)
        self.logdev = None
        self.sensors = None
        self.meas = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switch.
        Apply power to the unit's Battery terminals to power up the micro.

        """
        mes.dmm_lock.measure(timeout=5)
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        # Apply DC Source to Battery terminals
        dev.dcs_vbat.output(12.6, True)
        tester.MeasureGroup(
            (mes.dmm_vbatin, mes.dmm_3v3u), timeout=5)

    @oldteststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        dev.program_arm.program()

    @oldteststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Put device into manual control mode.

        """
        dev.j35.open()
        dev.j35.brand(self.variant['HwVer'], self.sernum, dev.rla_reset)
        dev.j35.manual_mode(True)   # Start the change to manual mode
        mes.arm_swver.measure()

    @oldteststep
    def _step_aux(self, dev, mes):
        """Test Auxiliary input."""
        dev.dcs_vaux.output(13.5, True)
        mes.dmm_vaux.measure(timeout=5)
        dev.dcl_bat.output(0.5, True)
        dev.j35['AUX_RELAY'] = True
        tester.MeasureGroup(
            (mes.dmm_vbatout, mes.arm_auxv, mes.arm_auxi), timeout=5)
        dev.j35['AUX_RELAY'] = False
        dev.dcs_vaux.output(0.0, False)
        dev.dcl_bat.output(0.0)

    @oldteststep
    def _step_solar(self, dev, mes):
        """Test Solar input."""
        dev.dcs_solar.output(13.5, True)
        dev.j35['SOLAR'] = True
        tester.MeasureGroup((mes.dmm_vbatout, mes.dmm_vair), timeout=5)
        dev.j35['SOLAR'] = False
        dev.dcs_solar.output(0.0, False)

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        dev.j35.manual_mode()     # Complete the change to manual mode
        if self.variant['Derate']:
            dev.j35.derate()      # Derate for lower output current
        dev.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (mes.dmm_acin, mes.dmm_vbus, mes.dmm_12vpri, mes.arm_vout_ov),
            timeout=5)
        dev.j35.dcdc_on()
        mes.dmm_vbat.measure(timeout=5)
        dev.dcs_vbat.output(0.0, False)
        tester.MeasureGroup(
            (mes.arm_vout_ov, mes.dmm_3v3, mes.dmm_15vs, mes.dmm_vbat,
             mes.dmm_fanOff, mes.arm_acv, mes.arm_acf, mes.arm_secT,
             mes.arm_vout, mes.arm_fan),
            timeout=5)
        dev.j35['FAN'] = 100
        mes.dmm_fanOn.measure(timeout=5)

    @oldteststep
    def _step_output(self, dev, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        dev.j35.load_set(set_on=True, loads=())   # All outputs OFF
        dev.dcl_out.output(1.0, True)  # A little load on the output
        mes.dmm_vloadoff.measure(timeout=2)
        for load in range(self.limits['LOAD_COUNT'].limit):  # One at a time ON
            with tester.PathName('L{0}'.format(load + 1)):
                dev.j35.load_set(set_on=True, loads=(load, ))
                mes.dmm_vload.measure(timeout=2)
        dev.j35.load_set(set_on=False, loads=())  # All outputs ON


    @oldteststep
    def _step_remote_sw(self, dev, mes):
        """Test the remote switch."""
        dev.rla_loadsw.set_on()
        mes.dmm_vloadoff(timeout=5),
        dev.rla_loadsw.set_off()
        mes.dmm_vload(timeout=5),

    @oldteststep
    def _step_load(self, dev, mes):
        """Test with load."""
        dev.dcl_out.binary(1.0, self.limits['LOAD_CURRENT'].limit, 5.0)
        for load in range(self.limits['LOAD_COUNT'].limit):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.arm_loads[load].measure(timeout=5)
        dev.dcl_bat.output(4.0, True)
        tester.MeasureGroup(
            (mes.dmm_vbatload, mes.arm_battI, ), timeout=5)

    @oldteststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes.ramp_ocp(timeout=5)
        dev.dcl_out.output(0.0)
        dev.dcl_bat.output(0.0)

    @oldteststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        tester.MeasureGroup(
            (mes.dmm_canpwr, mes.arm_can_bind, ), timeout=10)
        dev.j35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        dev.j35['CAN'] = CAN_ECHO
        echo_reply = dev.j35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self.sensors.mir_can.store(echo_reply)
        mes.rx_can.measure()


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
        self.dcs_vbat = tester.DCSource(devices['DCS2'])
        self.dcs_vaux = tester.DCSource(devices['DCS3'])
        self.dcs_solar = tester.DCSource(devices['DCS4'])
        self.dcl_out = tester.DCLoad(devices['DCL1'])
        self.dcl_bat = tester.DCLoad(devices['DCL5'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        self.rla_loadsw = tester.Relay(devices['RLA3'])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, ARM_BIN)
        self.program_arm = share.ProgramARM(
            ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the J35 console
        self.j35_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.j35_ser.port = ARM_PORT
        # J35 Console driver
        self.j35 = console.Console(self.j35_ser, fifo)

    def reset(self):
        """Reset instruments."""
        self.j35.close()
        # Switch off AC Source & discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_out.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_vbat, self.dcs_vaux, self.dcs_solar):
            dcs.output(0.0, False)
        for ld in (self.dcl_out, self.dcl_bat):
            ld.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, ):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(
            self._reset, sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        j35 = logical_devices.j35
        sensor = tester.sensor
        self.mir_can = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.olock = sensor.Res(dmm, high=17, low=8, rng=10000, res=0.1)
        self.oacin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.ovbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self.o12Vpri = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self.ovbat = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self.ovload = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.oaux = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.oair = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.o3V3U = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self.o15Vs = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self.ofan = sensor.Vdc(dmm, high=12, low=5, rng=100, res=0.01)
        self.ocanpwr = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.01)
        self.sernum = sensor.DataEntry(
            message=tester.translate('j35_initial', 'msgSnEntry'),
            caption=tester.translate('j35_initial', 'capSnEntry'))
        self.arm_swver = console.Sensor(
            j35, 'SW_VER', rdgtype=sensor.ReadingString)
        self.arm_auxv = console.Sensor(j35, 'AUX_V')
        self.arm_auxi = console.Sensor(j35, 'AUX_I')
        self.arm_vout_ov = console.Sensor(j35, 'VOUT_OV')
        self.arm_acv = console.Sensor(j35, 'AC_V')
        self.arm_acf = console.Sensor(j35, 'AC_F')
        self.arm_sect = console.Sensor(j35, 'SEC_T')
        self.arm_vout = console.Sensor(j35, 'BUS_V')
        self.arm_fan = console.Sensor(j35, 'FAN')
        self.arm_bati = console.Sensor(j35, 'BATT_I')
        self.arm_canbind = console.Sensor(j35, 'CAN_BIND')
        # Generate load current sensors
        self.load_count = limits['LOAD_COUNT'].limit
        self.arm_loads = []
        for i in range(self.load_count):
            s = console.Sensor(j35, 'LOAD_{}'.format(i + 1))
            self.arm_loads.append(s)
        low, high = limits['OCP'].limit
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl_bat, sensor=self.ovbat,
            detect_limit=(limits['InOCP'], ),
            start=low - 1, stop=high + 1, step=0.5, delay=0.2)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.mir_can.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_acin = Measurement(limits['ACin'], sense.oacin)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.ovbus)
        self.dmm_12vpri = Measurement(limits['12Vpri'], sense.o12Vpri)
        self.dmm_vload = Measurement(limits['Vload'], sense.ovload)
        self.dmm_vloadoff = Measurement(limits['VloadOff'], sense.ovload)
        self.dmm_vbatin = Measurement(limits['VbatIn'], sense.ovbat)
        self.dmm_vbatout = Measurement(limits['VbatOut'], sense.ovbat)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.ovbat)
        self.dmm_vbatload = Measurement(limits['VbatLoad'], sense.ovbat)
        self.dmm_vair = Measurement(limits['Vair'], sense.oair)
        self.dmm_vaux = Measurement(limits['Vaux'], sense.oaux)
        self.dmm_3v3u = Measurement(limits['3V3U'], sense.o3V3U)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_15vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_fanOn = Measurement(limits['FanOn'], sense.ofan)
        self.dmm_fanOff = Measurement(limits['FanOff'], sense.ofan)
        self.ui_sernum = Measurement(limits['SerNum'], sense.sernum)
        self.arm_swver = Measurement(limits['ARM-SwVer'], sense.arm_swver)
        self.arm_auxv = Measurement(limits['ARM-AuxV'], sense.arm_auxv)
        self.arm_auxi = Measurement(limits['ARM-AuxI'], sense.arm_auxi)
        self.arm_vout_ov = Measurement(limits['Vout_OV'], sense.arm_vout_ov)
        self.arm_acv = Measurement(limits['ARM-AcV'], sense.arm_acv)
        self.arm_acf = Measurement(limits['ARM-AcF'], sense.arm_acf)
        self.arm_secT = Measurement(limits['ARM-SecT'], sense.arm_sect)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.arm_vout)
        self.arm_fan = Measurement(limits['ARM-Fan'], sense.arm_fan)
        self.arm_battI = Measurement(limits['ARM-BattI'], sense.arm_bati)
        self.dmm_canpwr = Measurement(limits['CanPwr'], sense.ocanpwr)
        self.rx_can = Measurement(limits['CAN_RX'], sense.mir_can)
        self.arm_can_bind = Measurement(limits['CAN_BIND'], sense.arm_canbind)
        # Generate load current measurements
        self.arm_loads = ()
        for sen in sense.arm_loads:
            m = Measurement(limits['ARM-LoadI'], sen)
            self.arm_loads += (m, )
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
