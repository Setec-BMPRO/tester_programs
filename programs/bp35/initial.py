#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Initial Test Program."""

import os
import inspect
import time
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp,
    LimitBetween, LimitDelta, LimitPercent, LimitInteger
    )
import share
from . import console

ARM_VERSION = '2.0.16018.4543'
PIC_VERSION = '1.4.14454.271'
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
SOLAR_VSET_SETTLE = 0.05
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
VOUT_SET = 12.8
OCP_SET = 35.0
# This magic number is the OCP setpoint.
# 44000 is the inbuilt default, which we reduce, to increase OCP.
_OCP_MAGIC = round(44000 / 1.05)    # +5% adjustment
# Number of lines in startup banner
BANNER_LINES = 3

_COMMON = (
    LimitLow('FixtureLock', 200),
    LimitDelta('HwVer8', 4400.0, 250.0),  # Rev 8+
    LimitDelta('ACin', VAC, 5.0),
    LimitBetween('Vpfc', 401.0, 424.0),
    LimitBetween('12Vpri', 11.5, 13.0),
    LimitBetween('15Vs', 11.5, 13.0),
    LimitBetween('Vload', 12.0, 12.9),
    LimitLow('VloadOff', 0.5),
    LimitDelta('VbatIn', 12.0, 0.5),
    LimitBetween('Vbat', 12.2, 13.0),
    LimitDelta('Vaux', 13.4, 0.4),
    LimitDelta('3V3', 3.30, 0.05),
    LimitDelta('FanOn', 12.5, 0.5),
    LimitLow('FanOff', 0.5),
    LimitDelta('SolarVcc', 3.3, 0.1),
    LimitDelta('SolarVin', SOLAR_VIN, 0.5),
    LimitPercent('VsetPre', SOLAR_VSET, 6.0),
    LimitPercent('VsetPost', SOLAR_VSET, 1.5),
    LimitPercent('ARM-IoutPre', SOLAR_ICAL, 9.0),
    LimitPercent('ARM-IoutPost', SOLAR_ICAL, 3.0),
    LimitPercent('OCP', OCP_SET, 4.0),
    LimitLow('InOCP', 11.6),
    LimitRegExp('ARM-SwVer', '^{0}$'.format(ARM_VERSION.replace('.', r'\.'))),
    LimitDelta('ARM-AcV', VAC, 10.0),
    LimitDelta('ARM-AcF', 50.0, 1.0),
    LimitBetween('ARM-SecT', 8.0, 70.0),
    LimitDelta('ARM-Vout', 12.45, 0.45),
    LimitPercent('ARM-SolarVin-Pre', SOLAR_VIN, SOLAR_VIN_PRE_PERCENT),
    LimitPercent('ARM-SolarVin-Post', SOLAR_VIN, SOLAR_VIN_POST_PERCENT),
    LimitBetween('ARM-Fan', 0, 100),
    LimitDelta('ARM-LoadI', 2.1, 0.9),
    LimitDelta('ARM-BattI', IBATT, 1.0),
    LimitDelta('ARM-BusI', ILOAD + IBATT, 3.0),
    LimitPercent('ARM-AuxV', VAUX_IN, percent=2.0, delta=0.3,
        doc='ARM Aux voltage reading'),
    LimitBetween('ARM-AuxI', 0.0, 1.5),
    LimitInteger('ARM-RemoteClosed', 1),
    LimitRegExp('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    LimitRegExp('CAN_RX', r'^RRQ,32,0'),
    LimitInteger('CAN_BIND', _CAN_BIND),
    LimitInteger('SOLAR_ALIVE', 1),
    LimitInteger('SOLAR_RELAY', 1),
    LimitInteger('SOLAR_ERROR', 0),
    LimitInteger('Vout_OV', 0),     # Over-voltage not triggered
    )

LIMITS_SR = _COMMON

#LIMITS_PM = ()

#LIMITS_HA = _COMMON

# Variant specific configuration data. Indexed by test program parameter.
#   'Limits': Test limits.
#   'HwVer': Hardware version data.
CONFIG = {
    'SR': {
        'Limits': LIMITS_SR,
        'HwVer': (10, 1, 'A'),
        },
#    'PM': {
#        'Limits': LIMITS_PM,
#        'HwVer': (10, 2, 'A'),
#        },
#    'HA': {
#        'Limits': LIMITS_HA,
#        'HwVer': (10, 3, 'A'),
#        },
    }


class Initial(share.TestSequence):

    """BP35 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        self.config = CONFIG[self.parameter]
        super().open(
            self.config['Limits'], LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('ProgramPIC', self._step_program_pic, not self.fifo),
            TestStep('ProgramARM', self._step_program_arm, not self.fifo),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('SolarReg', self._step_solar_reg),
            TestStep('Aux', self._step_aux),
            TestStep('PowerUp', self._step_powerup),
            TestStep('Output', self._step_output),
            TestStep('RemoteSw', self._step_remote_sw),
            TestStep('OCP', self._step_ocp),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals and Solar Reg input
        to power up the micros.

        """
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self.measure(('dmm_lock', 'hardware8', ), timeout=5)
        # Apply DC Sources to Battery terminals and Solar Reg input
        dev['dcs_vbat'].output(VBAT_IN, True)
        dev['rla_vbat'].set_on()
        dev['dcs_sreg'].output(SOLAR_VIN, True)
        self.measure(('dmm_vbatin', 'dmm_3v3', 'dmm_solarvcc'), timeout=5)

    @share.teststep
    def _step_program_pic(self, dev, mes):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        dev['program_pic'].program()
        dev['dcs_sreg'].output(0.0)     # Switch off the Solar

    @share.teststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        dev['program_arm'].program()
        # Cold Reset microprocessor for units that are reprogrammed
        dcsource, load = dev['dcs_vbat'], dev['dcl_bat']
        dcsource.output(0.0)
        load.output(1.0)
        time.sleep(1)
        load.output(0.0)
        dcsource.output(VBAT_IN)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        bp35, reset = dev['bp35'], dev['rla_reset']
        bp35.open()
        reset.pulse(0.1)
        dev['dcs_sreg'].output(SOLAR_VIN)
        bp35.action(None, delay=1.5, expected=BANNER_LINES)  # Flush banner
        bp35['NVWIPE'] = True
        reset.pulse(0.1)
        bp35.action(None, delay=1.5, expected=BANNER_LINES)  # Flush banner
        bp35['HW_VER'] = self.config['HwVer']
        bp35['SER_ID'] = self.sernum
        bp35['NVWRITE'] = True
        bp35['SR_DEL_CAL'] = True
        bp35['SR_HW_VER'] = PIC_HW_VER
        reset.pulse(0.1)    # Reset is required because of HW_VER setting
        bp35.action(None, delay=1.5, expected=BANNER_LINES)  # Flush banner
        mes['arm_swver']()
        bp35.manual_mode(start=True) # Start the change to manual mode

    @share.teststep
    def _step_solar_reg(self, dev, mes):
        """Test & Calibrate the Solar Regulator board."""
        bp35 = dev['bp35']
        # Switch on fixture BCE282 to power Solar Reg input
        dev['rla_acsw'].set_on()
        dev['acsource'].output(voltage=VAC, output=True)
        dev['dcs_sreg'].output(0.0, output=False)
        self.measure(('arm_solar_alive', 'arm_vout_ov', ), timeout=5)
        # The SR needs V & I set to zero after power up or it won't start.
        bp35.solar_set(0, 0)
        # Now set the actual output settings
        bp35.solar_set(SOLAR_VSET, SOLAR_ISET)
        time.sleep(2)           # Wait for the Solar to start & overshoot
        bp35['VOUT_OV'] = 2     # Reset OVP Latch because of Solar overshoot
        # Read solar input voltage and patch ARM measurement limits
        solar_vin = mes['dmm_solarvin'](timeout=5).reading1
        mes['arm_solar_vin_pre'].testlimit = (
            LimitPercent(
                'ARM-SolarVin-Pre', solar_vin, SOLAR_VIN_PRE_PERCENT), )
        mes['arm_solar_vin_post'].testlimit = (
            LimitPercent(
                'ARM-SolarVin-Post', solar_vin, SOLAR_VIN_POST_PERCENT), )
        # Check that Solar Reg is error-free, the relay is ON, Vin reads ok
        self.measure(
            ('arm_solar_error', 'arm_solar_relay', 'arm_solar_vin_pre', ), timeout=5)
        # Wait for the voltage to settle
        vmeasured = mes['dmm_vsetpre'].stable(SOLAR_VSET_SETTLE).reading1
        bp35['SR_VCAL'] = vmeasured   # Calibrate output voltage setpoint
        bp35['SR_VIN_CAL'] = solar_vin  # Calibrate input voltage reading
        # New solar sw ver 182 is too dumb to change the setpoint until a
        # DIFFERENT voltage setpoint is given...
        bp35.solar_set(SOLAR_VSET - 0.05, SOLAR_ISET)
        time.sleep(0.2)
        bp35.solar_set(SOLAR_VSET, SOLAR_ISET)
        time.sleep(1)
        self.measure(('arm_solar_vin_post', 'dmm_vsetpost', ))
        dev['dcl_bat'].output(SOLAR_ICAL, True)
        mes['arm_ioutpre'](timeout=5)
        bp35['SR_ICAL'] = SOLAR_ICAL  # Calibrate current setpoint
        time.sleep(1)
        mes['arm_ioutpost'](timeout=5)
        dev['dcl_bat'].output(0.0)
        # Switch off fixture BCE282
        dev['acsource'].output(voltage=0.0)
        dev['rla_acsw'].set_off()

    @share.teststep
    def _step_aux(self, dev, mes):
        """Apply Auxiliary input."""
        bp35, source, load = dev['bp35'], dev['dcs_vaux'], dev['dcl_bat']
        source.output(VAUX_IN, output=True)
        load.output(0.5, delay=1.0)
        mes['dmm_vbatin'](timeout=1)
        bp35['AUX_RELAY'] = True
        self.measure(('dmm_vaux', 'arm_vaux', 'arm_iaux'), timeout=5)
        bp35['AUX_RELAY'] = False
        source.output(0.0, output=False)
        load.output(0.0)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with AC."""
        bp35 = dev['bp35']
        # Complete the change to manual mode
        bp35.manual_mode(vout=VOUT_SET, iout=OCP_SET)
        dev['acsource'].output(voltage=VAC, output=True)
        self.measure(('dmm_acin', 'dmm_pri12v'), timeout=10)
        bp35.power_on()
        # Wait for PFC overshoot to settle
        mes['dmm_vpfc'].stable(PFC_STABLE)
        mes['arm_vout_ov']()
        # Remove injected Battery voltage
        dev['rla_vbat'].set_off()
        dev['dcs_vbat'].output(0.0, output=False)
        # Is it now running on it's own?
        mes['arm_vout_ov']()
        self.measure(('dmm_3v3', 'dmm_15vs'), timeout=10)
        # Calibrate Vout setting and reading
        data = self.measure(('dmm_vbat', ), timeout=10)
        bp35['VSET_CAL'] = data.reading1
        bp35['VBUS_CAL'] = data.reading1
        bp35['NVWRITE'] = True

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        bp35 = dev['bp35']
        # All outputs OFF
        bp35.load_set(set_on=True, loads=())
        # A little load on the output.
        dev['dcl_out'].output(1.0, True)
        mes['dmm_vloadoff'](timeout=2)
        # One at a time ON
        for load in range(OUTPUTS):
            with tester.PathName('L{0}'.format(load + 1)):
                bp35.load_set(set_on=True, loads=(load, ))
                mes['dmm_vload'](timeout=2)
        # All outputs ON
        bp35.load_set(set_on=False, loads=())

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Test Remote Load Isolator Switch."""
        relay = dev['rla_loadsw']
        relay.set_on()
        mes['arm_remote'](timeout=5)
        relay.set_off()
        mes['dmm_vload'](timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test functions of the unit."""
        bp35 = dev['bp35']
        self.measure(
            ('arm_acv', 'arm_acf', 'arm_sect', 'arm_vout', 'arm_fan',
             'dmm_fanoff'), timeout=5)
        bp35['FAN'] = 100
        mes['dmm_fanon'](timeout=5)
        dev['dcl_out'].binary(1.0, ILOAD, 5.0)
        dev['dcl_bat'].output(IBATT, output=True)
        self.measure(('dmm_vbat', 'arm_ibat', 'arm_ibus', ), timeout=5)
        bp35['BUS_ICAL'] = ILOAD + IBATT    # Calibrate current reading
        bp35['OCP_CAL'] = _OCP_MAGIC        # Calibrate current setpoint
        bp35['NVWRITE'] = True
        for load in range(OUTPUTS):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['arm_loads'][load](timeout=5)
        mes['ramp_ocp'](timeout=5)
        dev['dcl_bat'].output(0.0)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        bp35 = dev['bp35']
        mes['arm_can_bind'](timeout=10)
        bp35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        bp35['CAN'] = CAN_ECHO
        echo_reply = bp35.port.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        rx_can = mes['rx_can']
        rx_can.sensor.store(echo_reply)
        rx_can.measure()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vbat', tester.DCSource, 'DCS2'),
                ('dcs_vaux', tester.DCSource, 'DCS3'),
                ('dcs_sreg', tester.DCSource, 'DCS4'),
                ('dcl_out', tester.DCLoad, 'DCL1'),
                ('dcl_bat', tester.DCLoad, 'DCL5'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_pic', tester.Relay, 'RLA3'),
                ('rla_loadsw', tester.Relay, 'RLA4'),
                ('rla_vbat', tester.Relay, 'RLA5'),
                ('rla_acsw', tester.Relay, 'RLA6'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_arm'] = share.ProgramARM(
            ARM_PORT, os.path.join(folder, ARM_FILE), crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # PIC device programmer
        self['program_pic'] = share.ProgramPIC(
            PIC_FILE, folder, '33FJ16GS402', self['rla_pic'])
        # Serial connection to the BP35 console
        bp35_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bp35_ser.port = ARM_PORT
        # BP35 Console driver
        self['bp35'] = console.Console(bp35_ser, verbose=False)
        # Apply power to fixture (Comms & Trek2) circuits.
        self['dcs_vcom'].output(12.0, True)

    def reset(self):
        """Reset instruments."""
        self['bp35'].close()
        # Switch off AC Source & discharge the unit
        self['acsource'].reset()
        self['dcl_bat'].output(2.0)
        time.sleep(1)
        self['discharge'].pulse()
        for dev in ('dcs_vbat', 'dcs_vaux', 'dcs_sreg', 'dcl_out', 'dcl_bat'):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_pic',
                    'rla_loadsw', 'rla_vbat', 'rla_acsw'):
            self[rla].set_off()

    def close(self):
        """Close logical devices."""
        self['dcs_vcom'].output(0, False)   # Remove power from fixture.
        super().close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['mir_can'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['acin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['vpfc'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
        self['vload'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['vbat'] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self['vset'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['pri12v'] = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self['o3v3'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self['fan'] = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self['hardware'] = sensor.Res(dmm, high=8, low=4, rng=100000, res=1)
        self['o15vs'] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self['lock'] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self['solarvcc'] = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self['solarvin'] = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bp35_initial', 'msgSnEntry'),
            caption=tester.translate('bp35_initial', 'capSnEntry'))
        # Console sensors
        bp35 = self.devices['bp35']
        for name, cmdkey in (
                ('arm_acv', 'AC_V'),
                ('arm_acf', 'AC_F'),
                ('arm_sect', 'SEC_T'),
                ('arm_vout', 'BUS_V'),
                ('arm_fan', 'FAN'),
                ('arm_canbind', 'CAN_BIND'),
                ('arm_ibat', 'BATT_I'),
                ('arm_ibus', 'BUS_I'),
                ('arm_vaux', 'AUX_V'),
                ('arm_iaux', 'AUX_I'),
                ('arm_solar_alive', 'SR_ALIVE'),
                ('arm_solar_relay', 'SR_RELAY'),
                ('arm_solar_error', 'SR_ERROR'),
                ('arm_vout_ov', 'VOUT_OV'),
                ('arm_iout', 'SR_IOUT'),
                ('arm_solar_vin', 'SR_VIN'),
                ('arm_remote', 'BATT_SWITCH'),
            ):
            self[name] = console.Sensor(bp35, cmdkey)
        self['arm_swver'] = console.Sensor(
            bp35, 'SW_VER', rdgtype=sensor.ReadingString)
        # Generate load current sensors
        loads = []
        for i in range(1, OUTPUTS + 1):
            loads.append(console.Sensor(bp35, 'LOAD_{0}'.format(i)))
        self['arm_loads'] = loads
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_bat'],
            sensor=self['vbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - ILOAD - 1,
            stop=high - ILOAD + 1,
            step=0.1, delay=0.1)
        self['ocp'].on_read = lambda value: value + ILOAD


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('hardware8', 'HwVer8', 'hardware', ''),
            ('rx_can', 'CAN_RX', 'mir_can', ''),
            ('dmm_lock', 'FixtureLock', 'lock', ''),
            ('dmm_acin', 'ACin', 'acin', ''),
            ('dmm_vpfc', 'Vpfc', 'vpfc', ''),
            ('dmm_pri12v', '12Vpri', 'pri12v', ''),
            ('dmm_15vs', '15Vs', 'o15vs', ''),
            ('dmm_vload', 'Vload', 'vload', ''),
            ('dmm_vloadoff', 'VloadOff', 'vload', ''),
            ('dmm_vbatin', 'VbatIn', 'vbat', ''),
            ('dmm_vbat', 'Vbat', 'vbat', ''),
            ('dmm_vsetpre', 'VsetPre', 'vset', ''),
            ('dmm_vsetpost', 'VsetPost', 'vset', ''),
            ('arm_ioutpre', 'ARM-IoutPre', 'arm_iout', ''),
            ('arm_ioutpost', 'ARM-IoutPost', 'arm_iout', ''),
            ('dmm_vaux', 'Vaux', 'vbat', ''),
            ('dmm_3v3', '3V3', 'o3v3', ''),
            ('dmm_fanon', 'FanOn', 'fan', ''),
            ('dmm_fanoff', 'FanOff', 'fan', ''),
            ('dmm_solarvcc', 'SolarVcc', 'solarvcc', ''),
            ('dmm_solarvin', 'SolarVin', 'solarvin', ''),
            ('ramp_ocp', 'OCP', 'ocp', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', ''),
            ('arm_acv', 'ARM-AcV', 'arm_acv', ''),
            ('arm_acf', 'ARM-AcF', 'arm_acf', ''),
            ('arm_sect', 'ARM-SecT', 'arm_sect', ''),
            ('arm_vout', 'ARM-Vout', 'arm_vout', ''),
            ('arm_fan', 'ARM-Fan', 'arm_fan', ''),
            ('arm_can_bind', 'CAN_BIND', 'arm_canbind', ''),
            ('arm_ibat', 'ARM-BattI', 'arm_ibat', ''),
            ('arm_ibus', 'ARM-BusI', 'arm_ibus', ''),
            ('arm_vaux', 'ARM-AuxV', 'arm_vaux', ''),
            ('arm_iaux', 'ARM-AuxI', 'arm_iaux', ''),
            ('arm_solar_alive', 'SOLAR_ALIVE', 'arm_solar_alive', ''),
            ('arm_solar_relay', 'SOLAR_RELAY', 'arm_solar_relay', ''),
            ('arm_solar_error', 'SOLAR_ERROR', 'arm_solar_error', ''),
            ('arm_vout_ov', 'Vout_OV', 'arm_vout_ov', ''),
            ('arm_solar_vin_pre', 'ARM-SolarVin-Pre', 'arm_solar_vin', ''),
            ('arm_solar_vin_post', 'ARM-SolarVin-Post', 'arm_solar_vin', ''),
            ('arm_remote', 'ARM-RemoteClosed', 'arm_remote', ''),
            ))
        # Generate load current measurements
        loads = []
        for sen in self.sensors['arm_loads']:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        self['arm_loads'] = loads
