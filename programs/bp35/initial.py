#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Initial Test Program."""

import os
import inspect
import time
import threading
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp,
    LimitBetween, LimitDelta, LimitPercent, LimitInteger
    )
import share
from . import console

ARM_VERSION = '2.0.16018.4543'
ARM_HW_VER = 10
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
OCP_MAGIC = round(44000 / 1.05)    # +5% adjustment
# Number of lines in startup banner
BANNER_LINES = 3
# SR Solar Reg settings
SR_VSET = 13.650
SR_VSET_SETTLE = 0.05
SR_ISET = 30.0
SR_ICAL = 10.0
SR_VIN = 20.0
SR_VIN_PRE_PERCENT = 6.0
SR_VIN_POST_PERCENT = 1.5
# PM Solar Reg settings
PM_ZERO_WAIT = 30     # Settling delay for zero calibration

_COMMON = (
    LimitLow('FixtureLock', 200, doc='Fixture microswitch pressed'),
    LimitDelta('HwVer8', 4400.0, 250.0, doc='Hardware Rev 8 or higher'),
    LimitDelta('ACin', VAC, 5.0, doc='Injected AC voltage'),
    LimitBetween('Vpfc', 401.0, 424.0, doc='PFC output voltage'),
    LimitBetween('12Vpri', 11.5, 13.0, doc='12V primary control rail'),
    LimitBetween('15Vs', 11.5, 13.0),
    LimitBetween('Vload', 12.0, 12.9, doc='Load output is ON'),
    LimitLow('VloadOff', 0.5, doc='Load output is OFF'),
    LimitDelta('VbatIn', 12.0, 0.5),
    LimitBetween('Vbat', 12.2, 13.0),
    LimitDelta('Vaux', 13.4, 0.4),
    LimitDelta('3V3', 3.30, 0.05, doc='Micro power supply'),
    LimitDelta('FanOn', 12.5, 0.5, doc='Fans ON'),
    LimitLow('FanOff', 0.5, doc='Fans OFF'),
    LimitPercent('OCP', OCP_SET, 4.0, doc='OCP setpoint'),
    LimitLow('InOCP', 11.6, doc='Output voltage to detect OCP'),
    LimitRegExp('ARM-SwVer', '^{0}$'.format(ARM_VERSION.replace('.', r'\.')),
        doc='Reported software version'),
    LimitDelta('ARM-AcV', VAC, 10.0, doc='AC voltage reported by ARM'),
    LimitDelta('ARM-AcF', 50.0, 1.0, doc='AC frequency reported by ARM'),
    LimitBetween('ARM-SecT', 8.0, 70.0),
    LimitDelta('ARM-Vout', 12.45, 0.45),
    LimitBetween('ARM-Fan', 0, 100, doc='Fan speed (%) reported by ARM'),
    LimitDelta('ARM-LoadI', 2.1, 0.9, doc='Load current reported by ARM'),
    LimitDelta('ARM-BattI', IBATT, 1.0, doc='Battery current reported by ARM'),
    LimitDelta('ARM-BusI', ILOAD + IBATT, 3.0),
    LimitPercent('ARM-AuxV', VAUX_IN, percent=2.0, delta=0.3,
        doc='ARM Aux voltage reading'),
    LimitBetween('ARM-AuxI', 0.0, 1.5, doc='AUX current reported by ARM'),
    LimitInteger('ARM-RemoteClosed', 1, doc='REMOTE input reported by ARM'),
    LimitRegExp('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$',
        doc='Valid serial number format'),
    LimitRegExp('CAN_RX', r'^RRQ,32,0', doc='Expected CAN message'),
    LimitInteger('CAN_BIND', _CAN_BIND, doc='CAN comms established'),
    LimitInteger('Vout_OV', 0, doc='Over-voltage not triggered'),
    )

_SR_SOLAR = (
    LimitDelta('SolarVcc', 3.3, 0.1, doc='Vcc on the PIC micro'),
    LimitDelta('SolarVin', SR_VIN, 0.5, doc='SR Solar input voltage'),
    LimitPercent('VsetPre', SR_VSET, 6.0,
        doc='SR Solar Vout before calibration'),
    LimitPercent('VsetPost', SR_VSET, 1.5,
        doc='SR Solar Vout after calibration'),
    LimitPercent('ARM-IoutPre', SR_ICAL, 9.0,
        doc='SR Solar Iout before calibration'),
    LimitPercent('ARM-IoutPost', SR_ICAL, 3.0,
        doc='SR Solar Iout before calibration'),
    LimitPercent('ARM-SolarVin-Pre', SR_VIN, SR_VIN_PRE_PERCENT,
        doc='SR Solar Vin before calibration'),
    LimitPercent('ARM-SolarVin-Post', SR_VIN, SR_VIN_POST_PERCENT,
        doc='SR Solar Vin before calibration'),
    LimitInteger('SR-Alive', 1, doc='SR Solar present'),
    LimitInteger('SR-Relay', 1, doc='SR Solar input relay ON'),
    LimitInteger('SR-Error', 0, doc='No SR Solar error'),
    )

_PM_SOLAR = (
    LimitInteger('PM-Alive', 1, doc='PM Solar present'),
    LimitDelta('ARM-PmSolarIz-Pre', 0, 0.6, doc='PM zero reading before cal'),
    LimitDelta('ARM-PmSolarIz-Post', 0, 0.1, doc='PM zero reading after cal'),
    )

# Variant specific configuration data. Indexed by test program parameter.
#   'Limits': Test limits.
#   'HwVer': Hardware version data.
CONFIG = {
    'SR': {
        'Limits': _COMMON + _SR_SOLAR,
        'HwVer': (ARM_HW_VER, 1, 'A'),
        },
    'PM': {
        'Limits': _COMMON + _PM_SOLAR,
        'HwVer': (ARM_HW_VER, 2, 'A'),
        },
    'HA': {
        'Limits': _COMMON + _SR_SOLAR,
        'HwVer': (ARM_HW_VER, 3, 'A'),
        },
    }


class Initial(share.TestSequence):

    """BP35 Initial Test Program."""

    sernum = None   # Unit Serial number
    pm = False      # True if this is a 'PM' solar version unit

    def open(self):
        """Prepare for testing."""
        self.config = CONFIG[self.parameter]
        self.pm = (self.parameter == 'PM')
        super().open(
            self.config['Limits'], LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep(
                'ProgramPIC', self._step_program_pic,
                not self.pm and not self.fifo),
            TestStep('ProgramARM', self._step_program_arm, not self.fifo),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('SrSolar', self._step_sr_solar, not self.pm),
            TestStep('Aux', self._step_aux),
            TestStep('PowerUp', self._step_powerup),
            TestStep('Output', self._step_output),
            TestStep('RemoteSw', self._step_remote_sw),
            TestStep('PmSolar', self._step_pm_solar, self.pm),
            TestStep('OCP', self._step_ocp),
            TestStep('CanBus', self._step_canbus),
            )

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals to power up the ARM.

        """
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self.measure(('dmm_lock', 'hardware8', ), timeout=5)
        dev['dcs_vbat'].output(VBAT_IN, True)
        dev['rla_vbat'].set_on()
        self.measure(('dmm_vbatin', 'dmm_3v3'), timeout=5)

    @share.teststep
    def _step_program_pic(self, dev, mes):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        dev['SR_LowPower'].output(SR_VIN, output=True)
        mes['dmm_solarvcc'](timeout=5)
        dev['program_pic'].program()
        dev['SR_LowPower'].output(0.0)

    @share.teststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        dev['program_arm'].program()
        # Cold Reset microprocessor for units that were already programmed
        dcsource, load = dev['dcs_vbat'], dev['dcl_bat']
        dcsource.output(0.0)
        load.output(1.0, delay=1)
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
        if not self.pm:
            dev['SR_LowPower'].output(SR_VIN)
        bp35.action(None, delay=1.5, expected=BANNER_LINES)
        bp35['NVWIPE'] = True
        reset.pulse(0.1)
        bp35.action(None, delay=1.5, expected=BANNER_LINES)
        bp35['HW_VER'] = self.config['HwVer']
        bp35['SER_ID'] = self.sernum
        bp35['NVWRITE'] = True
        if not self.pm:
            bp35['SR_DEL_CAL'] = True
            bp35['SR_HW_VER'] = PIC_HW_VER
        reset.pulse(0.1)    # Reset is required because of HW_VER setting
        bp35.action(None, delay=1.5, expected=BANNER_LINES)
        mes['arm_swver']()
        if self.pm:
            bp35['PM_RELAY'] = False
            time.sleep(0.5)
            bp35['PM_RELAY'] = True
            dev['PmTimer'].start()
        bp35.manual_mode(start=True)    # Start the change to manual mode

    @share.teststep
    def _step_sr_solar(self, dev, mes):
        """Test & Calibrate the Solar Regulator board."""
        bp35 = dev['bp35']
        dev['SR_HighPower'].output(True)
        dev['SR_LowPower'].output(0.0, output=False)
        self.measure(('arm_sr_alive', 'arm_vout_ov', ), timeout=5)
        # The SR needs V & I set to zero after power up or it won't start.
        bp35.sr_set(0, 0)
        # Now set the actual output settings
        bp35.sr_set(SR_VSET, SR_ISET, delay=2)
        bp35['VOUT_OV'] = 2     # Reset OVP Latch because of Solar overshoot
        # Read solar input voltage and patch measurement limits
        sr_vin = mes['dmm_solarvin'](timeout=5).reading1
        mes['arm_sr_vin_pre'].testlimit = (
            LimitPercent(
                'ARM-SolarVin-Pre', sr_vin, SR_VIN_PRE_PERCENT), )
        mes['arm_sr_vin_post'].testlimit = (
            LimitPercent(
                'ARM-SolarVin-Post', sr_vin, SR_VIN_POST_PERCENT), )
        # Check that Solar Reg is error-free, the relay is ON, Vin reads ok
        self.measure(
            ('arm_sr_error', 'arm_sr_relay', 'arm_sr_vin_pre', ),
            timeout=5)
        # Wait for the voltage to settle
        vmeasured = mes['dmm_vsetpre'].stable(SR_VSET_SETTLE).reading1
        bp35['SR_VCAL'] = vmeasured     # Calibrate output voltage setpoint
        bp35['SR_VIN_CAL'] = sr_vin     # Calibrate input voltage reading
        # Solar sw ver 182 will not change the setpoint until a DIFFERENT
        # voltage setpoint is given...
        bp35.sr_set(SR_VSET - 0.05, SR_ISET, delay=0.2)
        bp35.sr_set(SR_VSET, SR_ISET, delay=1)
        self.measure(('arm_sr_vin_post', 'dmm_vsetpost', ))
        dev['dcl_bat'].output(SR_ICAL, True)
        mes['arm_ioutpre'](timeout=5)
        bp35['SR_ICAL'] = SR_ICAL       # Calibrate current setpoint
        time.sleep(1)
        mes['arm_ioutpost'](timeout=5)
        dev['dcl_bat'].output(0.0)
        dev['SR_HighPower'].output(False)

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
        mes['arm_vout_ov']()
        # Is it now running on it's own?
        self.measure(('dmm_3v3', 'dmm_15vs'), timeout=10)
        # Calibrate Vout setting and reading
        v_actual = self.measure(('dmm_vbat', ), timeout=10).reading1
        bp35['VSET_CAL'] = v_actual
        bp35['VBUS_CAL'] = v_actual
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
    def _step_pm_solar(self, dev, mes):
        """PM type Solar regulator."""
        bp35 = dev['bp35']
        dev['PmTimer'].wait()
        self.measure(('arm_pm_alive', 'arm_pm_iz_pre', ))
        bp35['PM_ZEROCAL'] = 0
        bp35['NVWRITE'] = True
        mes['arm_pm_iz_post']()

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
        bp35['OCP_CAL'] = OCP_MAGIC         # Adjust current setpoint
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


class SrHighPower():

    """High power source to power the SR Solar Regulator.

    It is a BCE282 inside the fixture which is powered by the AC Source.
    A relay feeds the AC Source to either the BCE282 (ON) or to the BP35 (OFF).

    """

    def __init__(self, relay, acsource):
        """Create the High Power source."""
        self.relay = relay
        self.acsource = acsource

    def output(self, output=False):
        """Switch on the source."""
        if output:
            self.relay.set_on()
            self.acsource.output(voltage=240, output=True, delay=0.5)
        else:
            self.acsource.output(voltage=0.0)
            self.relay.set_off()


class PmTimer():

    """A timer to run the PM Solar ADC settling time."""

    _myevent = None
    _mytimer = None
    _wait_time = None

    def __init__(self, wait_time):
        """Create the Timer."""
        self._myevent = threading.Event()
        self._wait_time = wait_time

    def start(self):
        """Start the timer."""
        self._myevent.clear()
        self._mytimer = threading.Timer(self._wait_time, self._myevent.set)
        self._mytimer.start()

    def wait(self):
        """Wait for the timer to finish."""
        self._myevent.wait()

    def cancel(self):
        """Cancel the timer."""
        if self._mytimer:
            self._mytimer.cancel()
        self._mytimer = None


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
                ('SR_LowPower', tester.DCSource, 'DCS4'),
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
        # High power source for the SR Solar Regulator
        self['SR_HighPower'] = SrHighPower(self['rla_acsw'], self['acsource'])
        self['PmTimer'] = PmTimer(PM_ZERO_WAIT)
        # Apply power to fixture (Comms & Trek2) circuits.
        self['dcs_vcom'].output(12.0, True)
        self.add_closer(lambda: self['dcs_vcom'].output(0, False))

    def reset(self):
        """Reset instruments."""
        self['bp35'].close()
        self['PmTimer'].cancel()
        # Switch off AC Source & discharge the unit
        self['acsource'].reset()
        self['dcl_bat'].output(2.0, delay=1)
        self['discharge'].pulse()
        for dev in (
                'dcs_vbat', 'dcs_vaux', 'SR_LowPower', 'dcl_out', 'dcl_bat'):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_pic',
                    'rla_loadsw', 'rla_vbat', 'rla_acsw'):
            self[rla].set_off()


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
                ('arm_vout_ov', 'VOUT_OV'),
                ('arm_iout', 'SR_IOUT'),
                ('arm_remote', 'BATT_SWITCH'),
                # SR Solar Regulator
                ('arm_sr_alive', 'SR_ALIVE'),
                ('arm_sr_relay', 'SR_RELAY'),
                ('arm_sr_error', 'SR_ERROR'),
                ('arm_sr_vin', 'SR_VIN'),
                # PM Solar Regulator
                ('arm_pm_alive', 'PM_ALIVE'),
                ('arm_pm_iout', 'PM_IOUT'),
                ('arm_pm_iout_rev', 'PM_IOUT_REV'),
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
            ('dmm_vaux', 'Vaux', 'vbat', ''),
            ('dmm_3v3', '3V3', 'o3v3', ''),
            ('dmm_fanon', 'FanOn', 'fan', ''),
            ('dmm_fanoff', 'FanOff', 'fan', ''),
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
            ('arm_vout_ov', 'Vout_OV', 'arm_vout_ov', ''),
            ('arm_remote', 'ARM-RemoteClosed', 'arm_remote', ''),
            ))
        if self.parameter == 'PM':      # PM Solar Regulator
            self.create_from_names((
                ('arm_pm_alive', 'PM-Alive', 'arm_pm_alive', ''),
                ('arm_pm_iz_pre', 'ARM-PmSolarIz-Pre', 'arm_pm_iout', ''),
                ('arm_pm_iz_post', 'ARM-PmSolarIz-Post', 'arm_pm_iout', ''),
                ))
        else:                           # SR Solar Regulator
            self.create_from_names((
                ('dmm_solarvcc', 'SolarVcc', 'solarvcc', ''),
                ('dmm_solarvin', 'SolarVin', 'solarvin', ''),
                ('arm_sr_alive', 'SR-Alive', 'arm_sr_alive', ''),
                ('arm_sr_relay', 'SR-Relay', 'arm_sr_relay', ''),
                ('arm_sr_error', 'SR-Error', 'arm_sr_error', ''),
                ('arm_sr_vin_pre', 'ARM-SolarVin-Pre', 'arm_sr_vin', ''),
                ('arm_sr_vin_post', 'ARM-SolarVin-Post', 'arm_sr_vin', ''),
                ('dmm_vsetpre', 'VsetPre', 'vset', ''),
                ('dmm_vsetpost', 'VsetPost', 'vset', ''),
                ('arm_ioutpre', 'ARM-IoutPre', 'arm_iout', ''),
                ('arm_ioutpost', 'ARM-IoutPost', 'arm_iout', ''),
                ))
        # Generate load current measurements
        loads = []
        for sen in self.sensors['arm_loads']:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        self['arm_loads'] = loads
