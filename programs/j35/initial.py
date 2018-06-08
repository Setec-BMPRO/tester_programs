#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""J35 Initial Test Program."""

import os
import math
import inspect
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp, LimitBetween, LimitDelta,
    LimitPercent, LimitInteger, LimitBoolean
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """J35 Initial Test Program."""

    # ARM software image file
    arm_file = 'j35_{0}.bin'.format(config.J35.sw_version)
    # Injected voltages
    #  Battery bus
    vbat_inject = 12.6
    #  Aux or Solar inputs
    aux_solar_inject = 13.5
    # AC voltage powering the unit
    ac_volt = 240.0
    ac_freq = 50.0
    # Extra % error in OCP allowed before adjustment
    ocp_adjust_percent = 10.0
    # Output set point when running in manual mode
    vout_set = 12.8
    # Battery load current
    batt_current = 4.0
    # Load on each output channel
    load_per_output = 2.0
    # Test limits common to all versions
    _common = (
        LimitDelta('ACin', ac_volt, delta=5.0, doc='AC input voltage'),
        LimitDelta('Vbus', ac_volt * math.sqrt(2), delta=10.0,
            doc='Peak of AC input'),
        LimitBetween('12Vpri', 11.5, 13.0, doc='12Vpri rail'),
        LimitPercent('Vload', vout_set, percent=3.0,
            doc='AC-DC convertor voltage setpoint'),
        LimitLow('VloadOff', 0.5, doc='When output is OFF'),
        LimitDelta('VbatIn', vbat_inject, delta=1.0,
            doc='Voltage at Batt when 12.6V is injected into Batt'),
        LimitDelta('VfuseIn', vbat_inject, delta=1.0,
            doc='Voltage after fuse when 12.6V is injected into Batt'),
        LimitDelta('VbatOut', aux_solar_inject, delta=0.5,
            doc='Voltage at Batt when 13.5V is injected into Aux'),
        LimitDelta('Vbat', vout_set, delta=0.2,
            doc='Voltage at Batt when unit is running'),
        LimitPercent('VbatLoad', vout_set, percent=5.0,
            doc='Voltage at Batt when unit is running under load'),
        LimitDelta('Vair', aux_solar_inject, delta=0.5,
            doc='Voltage at Air when 13.5V is injected into Solar'),
        LimitPercent('3V3U', 3.30, percent=1.5,
            doc='3V3 unswitched when 12.6V is injected into Batt'),
        LimitPercent('3V3', 3.30, percent=1.5, doc='3V3 internal rail'),
        LimitBetween('15Vs', 11.5, 13.0, doc='15Vs internal rail'),
        LimitDelta('FanOn', vout_set, delta=1.0, doc='Fan running'),
        LimitLow('FanOff', 0.5, doc='Fan not running'),
        LimitRegExp(
            'ARM-SwVer', '^{0}$'.format(
                config.J35.sw_version.replace('.', r'\.')),
            doc='Arm Software version'),
        LimitPercent('ARM-AuxV', aux_solar_inject, percent=2.0, delta=0.3,
            doc='ARM Aux voltage reading'),
        LimitBetween('ARM-AuxI', 0.0, 1.5,
            doc='ARM Aux current reading'),
        LimitInteger('Vout_OV', 0, doc='Over-voltage not triggered'),
        LimitPercent('ARM-AcV', ac_volt, percent=4.0, delta=1.0,
            doc='ARM AC voltage reading'),
        LimitPercent('ARM-AcF', ac_freq, percent=4.0, delta=1.0,
            doc='ARM AC frequency reading'),
        LimitBetween('ARM-SecT', 8.0, 70.0,
            doc='ARM secondary temperature sensor'),
        LimitPercent('ARM-Vout', vout_set, percent=2.0, delta=0.1,
            doc='ARM measured Vout'),
        LimitBetween('ARM-Fan', 0, 100, doc='ARM fan speed'),
        LimitPercent('ARM-BattI', batt_current, percent=1.7, delta=1.0,
            doc='ARM battery current reading'),
        LimitDelta('ARM-LoadI', load_per_output, delta=0.9,
            doc='ARM output current reading'),
        LimitInteger('ARM-RemoteClosed', 1),
        LimitDelta('CanPwr', vout_set, delta=1.8,
            doc='CAN bus power supply'),
        LimitInteger('LOAD_SET', 0x5555555,
            doc='ARM output load enable setting'),
        LimitInteger('CAN_BIND', 1 << 28,
            doc='ARM reports CAN bus operational'),
        LimitRegExp('CAN_RX', '^RRQ,36,0',
            doc='Response to CAN echo message'),
        LimitLow('InOCP', vout_set - 1.2, doc='Output is in OCP'),
        LimitLow('FixtureLock', 200, doc='Test fixture lid microswitch'),
        LimitBoolean('Solar-Status', True,
            doc='Solar Comparator Status is set'),
        LimitBoolean('DetectCal', True, doc='Solar comparator calibrated'),
        )
    # Version specific configuration data. Indexed by test program parameter.
    config_data = {
        'A': {
            'Config': config.J35A,
            'Limits': _common + (
                LimitLow('LOAD_COUNT', config.J35A.output_count),
                LimitPercent(
                    'OCP_pre', config.J35A.ocp_set,
                    (ocp_adjust_percent + 4.0, ocp_adjust_percent + 10.0),
                    doc='OCP trip range before adjustment'),
                LimitPercent('OCP', config.J35A.ocp_set, (4.0, 10.0),
                    doc='OCP trip range after adjustment'),
                LimitPercent('SolarCutoffPre', 14.125, percent=6,
                    doc='Solar Cut-Off voltage threshold uncertainty'),
                LimitBetween('SolarCutoff', 13.75, 14.5,
                    doc='Solar Cut-Off voltage threshold range'),
                ),
            },
        'B': {
            'Config': config.J35B,
            'Limits': _common + (
                LimitLow('LOAD_COUNT', config.J35B.output_count),
                LimitPercent(
                    'OCP_pre', config.J35B.ocp_set,
                    (ocp_adjust_percent + 4.0, ocp_adjust_percent + 7.0),
                    doc='OCP trip range before adjustment'),
                LimitPercent('OCP', config.J35B.ocp_set, (4.0, 7.0),
                    doc='OCP trip range after adjustment'),
                LimitPercent('SolarCutoffPre', 14.125, percent=6,
                    doc='Solar Cut-Off voltage threshold uncertainty'),
                LimitBetween('SolarCutoff', 13.75, 14.5,
                    doc='Solar Cut-Off voltage threshold range'),
                ),
            },
        'C': {
            'Config': config.J35C,
            'Limits': _common + (
                LimitLow('LOAD_COUNT', config.J35C.output_count),
                LimitPercent(
                    'OCP_pre', config.J35C.ocp_set,
                    (ocp_adjust_percent + 4.0, ocp_adjust_percent + 7.0),
                    doc='OCP trip range before adjustment'),
                LimitPercent('OCP', config.J35C.ocp_set, (4.0, 7.0),
                    doc='OCP trip range after adjustment'),
                LimitPercent('SolarCutoffPre', 14.125, percent=6,
                    doc='Solar Cut-Off voltage threshold uncertainty'),
                LimitBetween('SolarCutoff', 13.75, 14.5,
                    doc='Solar Cut-Off voltage threshold range'),
                ),
            },
        'D': {
            'Config': config.J35D,
            'Limits': _common + (
                LimitLow('LOAD_COUNT', config.J35D.output_count),
                LimitPercent(
                    'OCP_pre', config.J35D.ocp_set,
                    (ocp_adjust_percent + 4.0, ocp_adjust_percent + 7.0),
                    doc='OCP trip range before adjustment'),
                LimitPercent('OCP', config.J35D.ocp_set, (4.0, 7.0),
                    doc='OCP trip range after adjustment'),
                LimitPercent('SolarCutoffPre', 14.3, percent=6,
                    doc='Solar Cut-Off voltage threshold uncertainty'),
                LimitBetween('SolarCutoff', 14.0, 14.6,
                    doc='Solar Cut-Off voltage threshold range'),
                ),
            },
        }
    config = None
    sernum = None

    def open(self, uut):
        """Prepare for testing."""
        self.config = self.config_data[self.parameter]['Config']
        super().open(
            self.config_data[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('ProgramARM', self.devices['program_arm'].program),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('Aux', self._step_aux),
            TestStep('Solar', self._step_solar, self.config.solar),
            TestStep('ManualMode', self._step_manualmode),
            TestStep('SolarComp', self._step_solarcomp, self.config.solar_comp),
            TestStep('PowerUp', self._step_powerup),
            TestStep('Output', self._step_output),
            TestStep('RemoteSw', self._step_remote_sw),
            TestStep('Load', self._step_load),
            TestStep('OCP', self._step_ocp),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switch.
        Apply power to the unit's Battery terminals to power up the micro.

        """
        mes['dmm_lock'](timeout=5)
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        # Apply DC Source to Battery terminals
        dev['dcs_vbat'].output(self.vbat_inject, True, delay=1.0)
        self.measure(('dmm_vbatin', 'dmm_vfusein', 'dmm_3v3u'), timeout=5)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Put device into manual control mode.

        """
        j35 = dev['j35']
        j35.open()
        j35.brand(self.config.hw_version, self.sernum, dev['rla_reset'])
        j35.manual_mode(start=True)     # Start the change to manual mode
        mes['arm_swver']()

    @share.teststep
    def _step_aux(self, dev, mes):
        """Test Auxiliary input."""
        dev['dcs_vaux'].output(self.aux_solar_inject, True)
        dev['dcl_bat'].output(0.5, True)
        j35 = dev['j35']
        j35['AUX_RELAY'] = True
        self.measure(('dmm_vbatout', 'arm_auxv', 'arm_auxi'), timeout=5)
        j35['AUX_RELAY'] = False
        dev['dcs_vaux'].output(0.0, False)
        dev['dcl_bat'].output(0.0)

    @share.teststep
    def _step_solar(self, dev, mes):
        """Test Solar input."""
        j35 = dev['j35']
        dev['dcs_solar'].output(self.aux_solar_inject, True)
        j35['SOLAR'] = True
        # Only the 'C' has Air Suspension
        measurement = 'dmm_vair' if self.parameter == 'C' else 'dmm_vbatout'
        mes[measurement](timeout=5)
        j35['SOLAR'] = False
        dev['dcs_solar'].output(0.0, False)

    @share.teststep
    def _step_manualmode(self, dev, mes):
        """Complete the change to manual mode"""
        j35 = dev['j35']
        j35.manual_mode(vout=self.vout_set, iout=self.config.ocp_set)

    @share.teststep
    def _step_solarcomp(self, dev, mes):
        """Calibrate the solar comparator."""
        j35 = dev['j35']
        dev['dcs_solar'].output(13.0, True, delay=1.0)
        j35['SOLAR'] = True
        j35['SOLAR_STATUS'] = False
        dmm_vsolar = mes['ramp_solar_pre']().reading1
        low, high = self.limits['SolarCutoff'].limit
        if (low <= dmm_vsolar <= high):
            reply = True
        else:
            reply = False
            if dmm_vsolar < low:
                j35['SOLAR_OFFSET'] = 2     # Increase cut-off voltage threshold
            if dmm_vsolar > high:
                j35['SOLAR_OFFSET'] = 1     # Decrease cut-off voltage threshold
            dmm_vsolar = mes['ramp_solar']().reading1
            if (low <= dmm_vsolar <= high):
                reply = True
        mes['detectcal'].sensor.store(reply)
        mes['detectcal']()
        j35['SOLAR'] = False
        dev['dcs_solar'].output(0.0, False)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        j35 = dev['j35']
        dev['acsource'].output(voltage=self.ac_volt, output=True)
        self.measure(
            ('dmm_acin', 'dmm_vbus', 'dmm_12vpri', 'arm_vout_ov'),
            timeout=5)
        j35.dcdc_on()
        mes['dmm_vbat'](timeout=5)
        dev['dcs_vbat'].output(0.0, False)
        self.measure(
            ('arm_vout_ov', 'dmm_3v3', 'dmm_15vs', 'dmm_vbat', 'dmm_fanOff',
             'arm_acv', 'arm_acf', 'arm_secT', 'arm_vout', 'arm_fan'),
            timeout=5)
        v_actual = self.measure(('dmm_vbat', ), timeout=10).reading1
        j35['VSET_CAL'] = v_actual  # Calibrate Vout setting and reading
        j35['VBUS_CAL'] = v_actual
        j35['NVWRITE'] = True
        j35['FAN'] = 100
        mes['dmm_fanOn'](timeout=5)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches."""
        j35 = dev['j35']
        j35.load_set(set_on=True, loads=())     # All outputs OFF
        dev['dcl_out'].output(1.0, True)        # A little load
        mes['dmm_vloadoff'](timeout=2)
        j35.load_set(set_on=False, loads=())    # All outputs ON

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Test the remote switch."""
        relay = dev['rla_loadsw']
        relay.set_on()
        mes['arm_remote'](timeout=5)
        relay.set_off()
        mes['dmm_vload'](timeout=5)

    @share.teststep
    def _step_load(self, dev, mes):
        """Test with load."""
        j35 = dev['j35']
        val = mes['arm_loadset']().reading1
        self._logger.debug('0x{:08X}'.format(int(val)))
        output_count = self.config.output_count
        dev['dcl_out'].binary(1.0, output_count * self.load_per_output, 5.0)
        for load in range(output_count):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['arm_loads'][load](timeout=5)
        # Calibrate current reading
        j35['BUS_ICAL'] = output_count * self.load_per_output
        j35['NVWRITE'] = True
        dev['dcl_bat'].output(self.batt_current, True)
        self.measure(('dmm_vbatload', 'arm_battI', ), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        j35 = dev['j35']
        ocp_actual = mes['ramp_ocp_pre']().reading1
        # Adjust current setpoint
        j35['OCP_CAL'] = round(
            j35.ocp_cal() * ocp_actual / self.config.ocp_set)
        j35['NVWRITE'] = True
        mes['ramp_ocp']()
        dev['dcl_out'].output(0.0)
        dev['dcl_bat'].output(0.0)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        self.measure(('dmm_canpwr', 'arm_can_bind', ), timeout=10)
        j35tunnel = dev['j35tunnel']
        j35tunnel.open()
        mes['TunnelSwVer']()
        j35tunnel.close()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vbat', tester.DCSource, 'DCS2'),
                ('dcs_vaux', tester.DCSource, 'DCS3'),
                ('dcs_solar', tester.DCSource, 'DCS4'),
                ('dcl_out', tester.DCLoad, 'DCL1'),
                ('dcl_bat', tester.DCLoad, 'DCL5'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_loadsw', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        arm_port = share.fixture.port('029242', 'ARM')
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_arm'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, Initial.arm_file),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Serial connection to the console
        j35_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        j35_ser.port = arm_port
        # J35 Console driver
        self['j35'] = console.DirectConsole(j35_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.DeviceID.j35)
        self['j35tunnel'] = console.TunnelConsole(tunnel)
        # Apply power to fixture circuits.
        self['dcs_vcom'].output(22.0, output=True, delay=2)
        self.add_closer(lambda: self['dcs_vcom'].output(0, False))

    def reset(self):
        """Reset instruments."""
        self['j35'].close()
        # Switch off AC Source & discharge the unit
        self['acsource'].reset()
        self['dcl_out'].output(2.0, delay=1)
        self['discharge'].pulse()
        for dev in ('dcs_vbat', 'dcs_vaux', 'dcs_solar', 'dcl_out', 'dcl_bat'):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_loadsw'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['olock'] = sensor.Res(dmm, high=17, low=8, rng=10000, res=0.1)
        self['oacin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self['ovbus'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self['o12Vpri'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self['ovbat'] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self['ovfuse'] = sensor.Vdc(dmm, high=14, low=4, rng=100, res=0.001)
        self['ovload'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['oair'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self['vsolar'] = sensor.Vdc(dmm, high=15, low=6, rng=100, res=0.001)
        self['o3V3U'] = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self['o3V3'] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self['o15Vs'] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self['ofan'] = sensor.Vdc(dmm, high=12, low=5, rng=100, res=0.01)
        self['ocanpwr'] = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.01)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('j35_initial', 'msgSnEntry'),
            caption=tester.translate('j35_initial', 'capSnEntry'))
        self['mircal'] = sensor.Mirror()
        # Console sensors
        j35 = self.devices['j35']
        j35tunnel = self.devices['j35tunnel']
        for name, cmdkey in (
                ('arm_auxv', 'AUX_V'),
                ('arm_auxi', 'AUX_I'),
                ('arm_vout_ov', 'VOUT_OV'),
                ('arm_acv', 'AC_V'),
                ('arm_acf', 'AC_F'),
                ('arm_sect', 'SEC_T'),
                ('arm_vout', 'BUS_V'),
                ('arm_fan', 'FAN'),
                ('arm_bati', 'BATT_I'),
                ('arm_canbind', 'CAN_BIND'),
                ('arm_loadset', 'LOAD_SET'),
                ('arm_remote', 'BATT_SWITCH'),
                ('arm_solar_status', 'SOLAR_STATUS'),
            ):
            self[name] = share.console.Sensor(j35, cmdkey)
        self['arm_swver'] = share.console.Sensor(
            j35, 'SW_VER', rdgtype=sensor.ReadingString)
        self['TunnelSwVer'] = share.console.Sensor(
            j35tunnel, 'SW_VER', rdgtype=sensor.ReadingString)
        # Generate load current sensors
        load_count = self.limits['LOAD_COUNT'].limit
        self['arm_loads'] = []
        for i in range(load_count):
            sen = share.console.Sensor(j35, 'LOAD_{0}'.format(i + 1))
            self['arm_loads'].append(sen)
        load_current = load_count * Initial.load_per_output
        # Pre-adjust OCP
        low, high = self.limits['OCP_pre'].limit
        self['ocp_pre'] = sensor.Ramp(
            stimulus=self.devices['dcl_bat'],
            sensor=self['ovbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - load_current - 1,
            stop=high - load_current + 1,
            step=0.1)
        self['ocp_pre'].on_read = lambda value: value + load_current
        # Post-adjust OCP
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_bat'],
            sensor=self['ovbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - load_current - 1,
            stop=high - load_current + 1,
            step=0.1)
        self['ocp'].on_read = lambda value: value + load_current
        # Solar comparator calibration
        low, high = self.limits['SolarCutoffPre'].limit
        self['solar_input'] = sensor.Ramp(
            stimulus=self.devices['dcs_solar'],
            sensor=self['arm_solar_status'],
            detect_limit=(self.limits['Solar-Status'], ),
            start=low - 0.15,
            stop=high + 0.15,
            step=0.25, delay=1.0,
            reset=False)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'olock', ''),
            ('dmm_acin', 'ACin', 'oacin', ''),
            ('dmm_vbus', 'Vbus', 'ovbus', ''),
            ('dmm_12vpri', '12Vpri', 'o12Vpri', ''),
            ('dmm_vload', 'Vload', 'ovload', ''),
            ('dmm_vloadoff', 'VloadOff', 'ovload', ''),
            ('dmm_vbatin', 'VbatIn', 'ovbat', ''),
            ('dmm_vfusein', 'VfuseIn', 'ovfuse', ''),
            ('dmm_vbatout', 'VbatOut', 'ovbat', ''),
            ('dmm_vbat', 'Vbat', 'ovbat', ''),
            ('dmm_vbatload', 'VbatLoad', 'ovbat', ''),
            ('dmm_vair', 'Vair', 'oair', ''),
            ('dmm_3v3u', '3V3U', 'o3V3U', ''),
            ('dmm_3v3', '3V3', 'o3V3', ''),
            ('dmm_15vs', '15Vs', 'o15Vs', ''),
            ('dmm_fanOn', 'FanOn', 'ofan', ''),
            ('dmm_fanOff', 'FanOff', 'ofan', ''),
            ('ramp_ocp_pre', 'OCP_pre', 'ocp_pre', ''),
            ('ramp_ocp', 'OCP', 'ocp', ''),
            ('ramp_solar_pre', 'SolarCutoffPre', 'solar_input', ''),
            ('ramp_solar', 'SolarCutoff', 'solar_input', ''),
            ('detectcal', 'DetectCal', 'mircal', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', ''),
            ('arm_auxv', 'ARM-AuxV', 'arm_auxv', ''),
            ('arm_auxi', 'ARM-AuxI', 'arm_auxi', ''),
            ('arm_vout_ov', 'Vout_OV', 'arm_vout_ov', ''),
            ('arm_acv', 'ARM-AcV', 'arm_acv', ''),
            ('arm_acf', 'ARM-AcF', 'arm_acf', ''),
            ('arm_secT', 'ARM-SecT', 'arm_sect', ''),
            ('arm_vout', 'ARM-Vout', 'arm_vout', ''),
            ('arm_fan', 'ARM-Fan', 'arm_fan', ''),
            ('arm_battI', 'ARM-BattI', 'arm_bati', ''),
            ('dmm_canpwr', 'CanPwr', 'ocanpwr', ''),
            ('arm_can_bind', 'CAN_BIND', 'arm_canbind', ''),
            ('arm_loadset', 'LOAD_SET', 'arm_loadset', ''),
            ('arm_remote', 'ARM-RemoteClosed', 'arm_remote', ''),
            ('TunnelSwVer', 'ARM-SwVer', 'TunnelSwVer', ''),
            ))
        # Generate load current measurements
        loads = []
        for sen in self.sensors['arm_loads']:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        self['arm_loads'] = loads
