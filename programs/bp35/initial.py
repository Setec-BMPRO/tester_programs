#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Initial Test Program."""

import os
import inspect
import logging
import time
from pydispatch import dispatcher
import tester
import share
from share import teststep
from . import console

ARM_VERSION = '1.2.14256.3912'
ARM_HW_VER = (9, 0, 'A')
PIC_VERSION = '1.1.13802.182'
PIC_HW_VER = 3

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_FILE = 'bp35_{0}.bin'.format(ARM_VERSION)
# dsPIC software image file
PIC_FILE = 'bp35sr_{0}.hex'.format(PIC_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28
# Solar Reg settings
SOLAR_VSET = 13.650
SOLAR_ISET = 30.0
SOLAR_ICAL = 10.0
SOLAR_VIN = 20.0
SOLAR_VIN_PRE_PERCENT = 6.0
SOLAR_VIN_POST_PERCENT = 1.5
# Injected Vbat & Vaux
VBAT_IN = 12.4
VAUX_IN = 13.5
# PFC settling level
PFC_STABLE = 0.05
# Converter loading
ILOAD = 28.0
IBATT = 4.0
# Other settings
VAC = 240.0
OUTPUTS = 14


class Initial(tester.TestSequence):

    """BP35 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.devices = physical_devices
        self.sernum = None
        self.support = None

    def open(self, sequence=None):
        """Prepare for testing."""
        self._logger.info('Open')
        self.support = Support(self.devices, self.fifo)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep(
                'ProgramPIC', self._step_program_pic, not self.fifo),
            tester.TestStep(
                'ProgramARM', self._step_program_arm, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('SolarReg', self._step_solar_reg),
            tester.TestStep('Aux', self._step_aux),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('CanBus', self._step_canbus),
            )
        super().open(sequence)
        # Apply power to fixture (Comms & Trek2) circuits.
        self.support.devices.dcs_vcom.output(12.0, True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        # Remove power from fixture circuits.
        self.support.devices.dcs_vcom.output(0, False)
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.support.reset()

    @teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals and Solar Reg input
        to power up the micros.

        """
        self.sernum = share.get_sernum(
            self.uuts, self.support.limits['SerNum'], mes.ui_sernum)
        tester.MeasureGroup(
            (mes.dmm_lock, mes.hardware8, ), timeout=5)
        # Apply DC Sources to Battery terminals and Solar Reg input
        dev.dcs_vbat.output(VBAT_IN, True)
        dev.rla_vbat.set_on()
        dev.dcs_sreg.output(SOLAR_VIN, True)
        tester.MeasureGroup(
            (mes.dmm_vbatin, mes.dmm_3v3, mes.dmm_solarvcc), timeout=5)

    @teststep
    def _step_program_pic(self, dev, mes):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        dev.program_pic.program()
        dev.dcs_sreg.output(0.0)  # Switch off the Solar

    @teststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        dev.program_arm.program()
        # Reset microprocessor for boards that need reprogramming by Service
        dev.dcs_vbat.output(0.0)
        dev.dcl_bat.output(1.0)
        time.sleep(1)
        dev.dcl_bat.output(0.0)
        dev.dcs_vbat.output(VBAT_IN)

    @teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        bp35 = dev.bp35
        bp35.open()
        dev.rla_reset.pulse(0.1)
        dev.dcs_sreg.output(SOLAR_VIN)
        bp35.action(None, delay=1.5, expected=2)  # Flush banner
        bp35['UNLOCK'] = True
        bp35['HW_VER'] = ARM_HW_VER
        bp35['SER_ID'] = self.sernum
        bp35['NVDEFAULT'] = True
        bp35['NVWRITE'] = True
        bp35['SR_DEL_CAL'] = True
        bp35['SR_HW_VER'] = PIC_HW_VER
        # Restart required because of HW_VER setting
        dev.rla_reset.pulse(0.1)
        bp35.action(None, delay=1.5, expected=2)  # Flush banner
        bp35['UNLOCK'] = True
        mes.arm_swver.measure()
        bp35.manual_mode()

    @teststep
    def _step_solar_reg(self, dev, mes):
        """Test & Calibrate the Solar Regulator board."""
        bp35 = dev.bp35
        # Switch on fixture BCE282 to power Solar Reg input
        dev.rla_acsw.set_on()
        dev.acsource.output(voltage=VAC, output=True)
        dev.dcs_sreg.output(0.0, output=False)
        tester.MeasureGroup((mes.arm_solar_alive, mes.arm_vout_ov, ))
        # The SR needs V & I set to zero after power up or it won't start.
        bp35.solar_set(0, 0)
        # Now set the actual output settings
        bp35.solar_set(SOLAR_VSET, SOLAR_ISET)
        time.sleep(2)           # Wait for the Solar to start & overshoot
        bp35['VOUT_OV'] = 2     # Reset OVP Latch because the Solar overshot
        # Read solar input voltage and setup ARM measurement limits
        solar_vin = mes.dmm_solarvin.measure(timeout=5).reading1
        mes.arm_solar_vin_pre.testlimit = (
            tester.testlimit.LimitHiLoPercent(
                'ARM-SolarVin-Pre',
                (solar_vin, SOLAR_VIN_PRE_PERCENT)), )
        mes.arm_solar_vin_post.testlimit = (
            tester.testlimit.LimitHiLoPercent(
                'ARM-SolarVin-Post',
                (solar_vin, SOLAR_VIN_POST_PERCENT)), )
        # Check that Solar Reg is error-free, the relay is ON, Vin reads ok
        tester.MeasureGroup(
            (mes.arm_solar_error, mes.arm_solar_relay,
             mes.arm_solar_vin_pre, ))
        vmeasured = mes.dmm_vsetpre.measure(timeout=5).reading1
        bp35['SR_VCAL'] = vmeasured   # Calibrate output voltage setpoint
        bp35['SR_VIN_CAL'] = solar_vin  # Calibrate input voltage reading
        # New solar sw ver 182 is too dumb to change the setpoint until a
        # DIFFERENT voltage setpoint is given...
        bp35.solar_set(SOLAR_VSET - 0.05, SOLAR_ISET)
        bp35.solar_set(SOLAR_VSET, SOLAR_ISET)
        time.sleep(1)
        tester.MeasureGroup(
            (mes.arm_solar_vin_post, mes.dmm_vsetpost, ))
        dev.dcl_bat.output(SOLAR_ICAL, True)
        mes.arm_ioutpre.measure(timeout=5)
        bp35['SR_ICAL'] = SOLAR_ICAL  # Calibrate current setpoint
        time.sleep(1)
        mes.arm_ioutpost.measure(timeout=5)
        dev.dcl_bat.output(0.0)
        # Switch off fixture BCE282
        dev.acsource.output(voltage=0.0)
        dev.rla_acsw.set_off()

    @teststep
    def _step_aux(self, dev, mes):
        """Apply Auxiliary input."""
        bp35 = dev.bp35
        dev.dcs_vaux.output(VAUX_IN, output=True)
        dev.dcl_bat.output(0.5)
        bp35['AUX_RELAY'] = True
        tester.MeasureGroup(
            (mes.dmm_vaux, mes.arm_vaux, mes.arm_iaux), timeout=5)
        bp35['AUX_RELAY'] = False
        dev.dcs_vaux.output(0.0, output=False)
        dev.dcl_bat.output(0.0)

    @teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        dev.acsource.output(voltage=VAC, output=True)
        tester.MeasureGroup((mes.dmm_acin, mes.dmm_pri12v), timeout=10)
        dev.bp35.power_on()
        # Wait for PFC overshoot to settle
        mes.dmm_vpfc.stable(PFC_STABLE)
        mes.arm_vout_ov.measure()
        # Remove injected Battery voltage
        dev.rla_vbat.set_off()
        dev.dcs_vbat.output(0.0, output=False)
        # Is it now running on it's own?
        mes.arm_vout_ov.measure()
        tester.MeasureGroup(
            (mes.dmm_3v3, mes.dmm_15vs, mes.dmm_vbat), timeout=10)

    @teststep
    def _step_output(self, dev, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        bp35 = dev.bp35
        # All outputs OFF
        bp35.load_set(set_on=True, loads=())
        # A little load on the output.
        dev.dcl_out.output(1.0, True)
        mes.dmm_vloadoff.measure(timeout=2)
        # One at a time ON
        for load in range(OUTPUTS):
            with tester.PathName('L{0}'.format(load + 1)):
                bp35.load_set(set_on=True, loads=(load, ))
                mes.dmm_vload.measure(timeout=2)
        # All outputs ON
        bp35.load_set(set_on=False, loads=())

    @teststep
    def _step_remote_sw(self, dev, mes):
        """Test Remote Load Isolator Switch."""
        dev.rla_loadsw.set_on()
        mes.dmm_vloadoff.measure(timeout=5)
        dev.rla_loadsw.set_off()
        mes.dmm_vload.measure(timeout=5)

    @teststep
    def _step_ocp(self, dev, mes):
        """Test functions of the unit."""
        tester.MeasureGroup(
            (mes.arm_acv, mes.arm_acf, mes.arm_sect, mes.arm_vout,
             mes.arm_fan, mes.dmm_fanoff), timeout=5)
        dev.bp35['FAN'] = 100
        mes.dmm_fanon.measure(timeout=5)
        dev.dcl_out.binary(1.0, ILOAD, 5.0)
        dev.dcl_bat.output(IBATT, output=True)
        tester.MeasureGroup(
            (mes.dmm_vbat, mes.arm_ibat, mes.arm_ibus, ), timeout=5)
        dev.bp35['BUS_ICAL'] = ILOAD + IBATT    # Calibrate converter current
        for load in range(OUTPUTS):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.arm_loads[load].measure(timeout=5)
        mes.ramp_ocp.measure(timeout=5)
        dev.dcl_bat.output(0.0)

    @teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes.arm_can_bind.measure(timeout=10)
        dev.bp35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(CAN_ECHO))
        dev.bp35['CAN'] = CAN_ECHO
        echo_reply = dev.bp35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        self.support.sensors.mir_can.store(echo_reply)
        mes.rx_can.measure()


class Support():

    """Supporting data."""

    def __init__(self, physical_devices, fifo):
        """Create all supporting classes."""
        self.devices = LogicalDevices(physical_devices, fifo)
        self.limits = tester.limitdict((
            tester.LimitLo('FixtureLock', 50),
            tester.LimitHiLoDelta('HwVer8', (4400.0, 250.0)),  # Rev 8+
            tester.LimitHiLoDelta('ACin', (VAC, 5.0)),
            tester.LimitHiLo('Vpfc', (401.0, 424.0)),
            tester.LimitHiLo('12Vpri', (11.5, 13.0)),
            tester.LimitHiLo('15Vs', (11.5, 13.0)),
            tester.LimitHiLo('Vload', (12.0, 12.9)),
            tester.LimitLo('VloadOff', 0.5),
            tester.LimitHiLoDelta('VbatIn', (12.0, 0.5)),
            tester.LimitHiLo('Vbat', (12.2, 13.0)),
            tester.LimitHiLoDelta('Vaux', (13.4, 0.4)),
            tester.LimitHiLoDelta('3V3', (3.30, 0.05)),
            tester.LimitHiLoDelta('FanOn', (12.5, 0.5)),
            tester.LimitLo('FanOff', 0.5),
            tester.LimitHiLoDelta('SolarVcc', (3.3, 0.1)),
            tester.LimitHiLoDelta('SolarVin', (SOLAR_VIN, 0.5)),
            tester.LimitHiLoPercent('VsetPre', (SOLAR_VSET, 6.0)),
            tester.LimitHiLoPercent('VsetPost', (SOLAR_VSET, 1.5)),
            tester.LimitHiLoPercent('ARM-IoutPre', (SOLAR_ICAL, 9.0)),
            tester.LimitHiLoPercent('ARM-IoutPost', (SOLAR_ICAL, 3.0)),
            tester.LimitHiLo('OCP', (34.0 - ILOAD, 37.0 - ILOAD)),
            tester.LimitLo('InOCP', 11.6),
            tester.LimitString(
                'ARM-SwVer', '^{0}$'.format(ARM_VERSION.replace('.', r'\.'))),
            tester.LimitHiLoDelta('ARM-AcV', (VAC, 10.0)),
            tester.LimitHiLoDelta('ARM-AcF', (50.0, 1.0)),
            tester.LimitHiLo('ARM-SecT', (8.0, 70.0)),
            tester.LimitHiLoDelta('ARM-Vout', (12.45, 0.45)),
            tester.LimitHiLoPercent(
                'ARM-SolarVin-Pre', (SOLAR_VIN, SOLAR_VIN_PRE_PERCENT)),
            tester.LimitHiLoPercent(
                'ARM-SolarVin-Post', (SOLAR_VIN, SOLAR_VIN_POST_PERCENT)),
            tester.LimitHiLo('ARM-Fan', (0, 100)),
            tester.LimitHiLoDelta('ARM-LoadI', (2.1, 0.9)),
            tester.LimitHiLoDelta('ARM-BattI', (IBATT, 1.0)),
            tester.LimitHiLoDelta('ARM-BusI', (ILOAD + IBATT, 3.0)),
            tester.LimitHiLoDelta('ARM-AuxV', (13.4, 0.4)),
            tester.LimitHiLo('ARM-AuxI', (0.0, 1.5)),
            tester.LimitString('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
            tester.LimitString('CAN_RX', r'^RRQ,32,0'),
            tester.LimitHiLoInt('CAN_BIND', _CAN_BIND),
            tester.LimitHiLoInt('SOLAR_ALIVE', 1),
            tester.LimitHiLoInt('SOLAR_RELAY', 1),
            tester.LimitHiLoInt('SOLAR_ERROR', 0),
            tester.LimitHiLoInt('Vout_OV', 0),     # Over-voltage not triggered
            ))
        self.sensors = Sensors(self.devices, self.limits)
        self.measurements = Measurements(self.sensors, self.limits)

    def reset(self):
        """Reset instruments."""
        self.devices.reset()


class LogicalDevices(share.AttrDict):

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        super().__init__(self.__class__.__name__)
        self.fifo = fifo
        self.save('dmm', tester.DMM(devices['DMM']))
        self.save('acsource', tester.ACSource(devices['ACS']))
        self.save('discharge', tester.Discharge(devices['DIS']))
        self.save('dcs_vcom', tester.DCSource(devices['DCS1']))
        self.save('dcs_vbat', tester.DCSource(devices['DCS2']))
        self.save('dcs_vaux', tester.DCSource(devices['DCS3']))
        self.save('dcs_sreg', tester.DCSource(devices['DCS4']))
        self.save('dcl_out', tester.DCLoad(devices['DCL1']))
        self.save('dcl_bat', tester.DCLoad(devices['DCL5']))
        self.save('rla_reset', tester.Relay(devices['RLA1']))
        self.save('rla_boot', tester.Relay(devices['RLA2']))
        self.save('rla_pic', tester.Relay(devices['RLA3']))
        self.save('rla_loadsw', tester.Relay(devices['RLA4']))
        self.save('rla_vbat', tester.Relay(devices['RLA5']))
        self.save('rla_acsw', tester.Relay(devices['RLA6']))
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.save('program_arm', share.ProgramARM(
            ARM_PORT, os.path.join(folder, ARM_FILE), crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset))
        # PIC device programmer
        self.save('program_pic', share.ProgramPIC(
            PIC_FILE, folder, '33FJ16GS402', self.rla_pic))
        # Serial connection to the BP35 console
        self.save('bp35_ser', tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0))
        # Set port separately, as we don't want it opened yet
        self.bp35_ser.port = ARM_PORT
        # BP35 Console driver
        self.save('bp35', console.Console(self.bp35_ser))

    def bp35_puts(self,
                  string_data, preflush=0, postflush=0, priority=False,
                  addprompt=True):
        """Push string data into the BP35 buffer if FIFOs are enabled."""
        if self.fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.bp35.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.bp35.close()
        # Switch off AC Source & discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_bat.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_vbat, self.dcs_vaux, self.dcs_sreg):
            dcs.output(0.0, False)
        for load in (self.dcl_out, self.dcl_bat):
            load.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_pic,
                    self.rla_loadsw, self.rla_vbat, self.rla_acsw):
            rla.set_off()


class Sensors(share.AttrDict):

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        super().__init__(self.__class__.__name__)
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        bp35 = logical_devices.bp35
        sensor = tester.sensor
        self.save('mir_can', sensor.Mirror(rdgtype=sensor.ReadingString))
        self.save('acin', sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01))
        self.save('vpfc', sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001))
        self.save('vload', sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001))
        self.save('vbat', sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001))
        self.save('vset', sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001))
        self.save(
            'pri12v', sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001))
        self.save('o3v3', sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001))
        self.save('fan', sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01))
        self.save(
            'hardware', sensor.Res(dmm, high=8, low=4, rng=100000, res=1))
        self.save('o15vs', sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01))
        self.save('lock', sensor.Res(dmm, high=10, low=6, rng=10000, res=1))
        self.save(
            'solarvcc', sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001))
        self.save(
            'solarvin', sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001))
        self.save('ocp', sensor.Ramp(
            stimulus=logical_devices.dcl_bat, sensor=self.vbat,
            detect_limit=(limits['InOCP'], ),
            start=4.0, stop=10.0, step=0.5, delay=0.1))
        self.save('sernum', sensor.DataEntry(
            message=tester.translate('bp35_initial', 'msgSnEntry'),
            caption=tester.translate('bp35_initial', 'capSnEntry')))
        self.save('arm_swver', console.Sensor(
            bp35, 'SW_VER', rdgtype=sensor.ReadingString))
        self.save('arm_acv', console.Sensor(bp35, 'AC_V'))
        self.save('arm_acf', console.Sensor(bp35, 'AC_F'))
        self.save('arm_sect', console.Sensor(bp35, 'SEC_T'))
        self.save('arm_vout', console.Sensor(bp35, 'BUS_V'))
        self.save('arm_fan', console.Sensor(bp35, 'FAN'))
        self.save('arm_canbind', console.Sensor(bp35, 'CAN_BIND'))
        # Generate load current sensors
        loads = []
        for i in range(1, OUTPUTS + 1):
            loads.append(console.Sensor(bp35, 'LOAD_{0}'.format(i)))
        self.save('arm_loads', loads)
        self.save('arm_ibat', console.Sensor(bp35, 'BATT_I'))
        self.save('arm_ibus', console.Sensor(bp35, 'BUS_I'))
        self.save('arm_vaux', console.Sensor(bp35, 'AUX_V'))
        self.save('arm_iaux', console.Sensor(bp35, 'AUX_I'))
        self.save('arm_solar_alive', console.Sensor(bp35, 'SR_ALIVE'))
        self.save('arm_solar_relay', console.Sensor(bp35, 'SR_RELAY'))
        self.save('arm_solar_error', console.Sensor(bp35, 'SR_ERROR'))
        self.save('arm_vout_ov', console.Sensor(bp35, 'VOUT_OV'))
        self.save('arm_iout', console.Sensor(bp35, 'SR_IOUT'))
        self.save('arm_solar_vin', console.Sensor(bp35, 'SR_VIN'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.mir_can.flush()


class Measurements(share.AttrDict):

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        super().__init__(self.__class__.__name__)
        self.limits = limits
        self.save('hardware8', 'HwVer8', sense.hardware)
        self.save('rx_can', 'CAN_RX', sense.mir_can)
        self.save('dmm_lock', 'FixtureLock', sense.lock)
        self.save('dmm_acin', 'ACin', sense.acin)
        self.save('dmm_vpfc', 'Vpfc', sense.vpfc)
        self.save('dmm_pri12v', '12Vpri', sense.pri12v)
        self.save('dmm_15vs', '15Vs', sense.o15vs)
        self.save('dmm_vload', 'Vload', sense.vload)
        self.save('dmm_vloadoff', 'VloadOff', sense.vload)
        self.save('dmm_vbatin', 'VbatIn', sense.vbat)
        self.save('dmm_vbat', 'Vbat', sense.vbat)
        self.save('dmm_vsetpre', 'VsetPre', sense.vset)
        self.save('dmm_vsetpost', 'VsetPost', sense.vset)
        self.save('arm_ioutpre', 'ARM-IoutPre', sense.arm_iout)
        self.save('arm_ioutpost', 'ARM-IoutPost', sense.arm_iout)
        self.save('dmm_vaux', 'Vaux', sense.vbat)
        self.save('dmm_3v3', '3V3', sense.o3v3)
        self.save('dmm_fanon', 'FanOn', sense.fan)
        self.save('dmm_fanoff', 'FanOff', sense.fan)
        self.save('dmm_solarvcc', 'SolarVcc', sense.solarvcc)
        self.save('dmm_solarvin', 'SolarVin', sense.solarvin)
        self.save('ramp_ocp', 'OCP', sense.ocp)
        self.save('ui_sernum', 'SerNum', sense.sernum)
        self.save('arm_swver', 'ARM-SwVer', sense.arm_swver)
        self.save('arm_acv', 'ARM-AcV', sense.arm_acv)
        self.save('arm_acf', 'ARM-AcF', sense.arm_acf)
        self.save('arm_sect', 'ARM-SecT', sense.arm_sect)
        self.save('arm_vout', 'ARM-Vout', sense.arm_vout)
        self.save('arm_fan', 'ARM-Fan', sense.arm_fan)
        self.save('arm_can_bind', 'CAN_BIND', sense.arm_canbind)
        # Generate load current measurements
        loads = []
        for sen in sense.arm_loads:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        super().save('arm_loads', loads)
        self.save('arm_ibat', 'ARM-BattI', sense.arm_ibat)
        self.save('arm_ibus', 'ARM-BusI', sense.arm_ibus)
        self.save('arm_vaux', 'ARM-AuxV', sense.arm_vaux)
        self.save('arm_iaux', 'ARM-AuxI', sense.arm_iaux)
        self.save(
            'arm_solar_alive', 'SOLAR_ALIVE', sense.arm_solar_alive)
        self.save(
            'arm_solar_relay', 'SOLAR_RELAY', sense.arm_solar_relay)
        self.save(
            'arm_solar_error', 'SOLAR_ERROR', sense.arm_solar_error)
        self.save('arm_vout_ov', 'Vout_OV', sense.arm_vout_ov)
        self.save(
            'arm_solar_vin_pre', 'ARM-SolarVin-Pre', sense.arm_solar_vin)
        self.save(
            'arm_solar_vin_post', 'ARM-SolarVin-Post', sense.arm_solar_vin)

    def save(self, name, limitname, sensor, position_fail=True):
        """Create a Measurement.

        @param name Measurement name
        @param limitname Test Limit name
        @param sensor Sensor to use
        @return tester.Measurement instance

        """
        if not position_fail:
            self.limits[limitname].position_fail = False
        super().save(name, tester.Measurement(self.limits[limitname], sensor))
