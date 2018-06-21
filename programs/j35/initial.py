#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""J35 Initial Test Program."""

import os
import inspect
import serial
import tester
from tester import TestStep
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """J35 Initial Test Program."""

    def open(self, uut):
        """Prepare for testing."""
        self.cfg = config.J35.select(self.parameter, uut)
        limits = self.cfg.limits_initial()
        Sensors.output_count = self.cfg.output_count
        Sensors.load_per_output = self.cfg.load_per_output
        Devices.sw_version = self.cfg.sw_version
        super().open(limits, Devices, Sensors, Measurements)
        self.limits['SwVer'].adjust(
            '^{0}$'.format(self.cfg.sw_version.replace('.', r'\.')))
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('ProgramARM', self.devices['program_arm'].program),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('Aux', self._step_aux),
            TestStep('Solar', self._step_solar, self.cfg.solar),
            TestStep('ManualMode', self._step_manualmode),
            TestStep('SolarComp', self._step_solarcomp, self.cfg.solar_comp),
            TestStep('PowerUp', self._step_powerup),
            TestStep('Output', self._step_output),
            TestStep('RemoteSw', self._step_remote_sw),
            TestStep('Load', self._step_load),
            TestStep('OCP', self._step_ocp),
            TestStep('CanBus', self._step_canbus, self.cfg.canbus),
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
        dev['dcs_vbat'].output(self.cfg.vbat_inject, True, delay=1.0)
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
        j35.brand(self.cfg.hw_version, self.sernum, dev['rla_reset'])
        j35.manual_mode(start=True)     # Start the change to manual mode
        mes['arm_swver']()

    @share.teststep
    def _step_aux(self, dev, mes):
        """Test Auxiliary input."""
        dev['dcs_vaux'].output(self.cfg.aux_solar_inject, True)
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
        dev['dcs_solar'].output(self.cfg.aux_solar_inject, True)
        j35['SOLAR'] = True
        # Only the 'C' & 'D' have Air Suspension
        measurement = (
            'dmm_vair'
            if self.parameter in ('C', 'D', )
            else 'dmm_vbatout'
            )
        mes[measurement](timeout=5)
        j35['SOLAR'] = False
        dev['dcs_solar'].output(0.0, False)

    @share.teststep
    def _step_manualmode(self, dev, mes):
        """Complete the change to manual mode"""
        j35 = dev['j35']
        j35.manual_mode(vout=self.cfg.vout_set, iout=self.cfg.ocp_set)

    @share.teststep
    def _step_solarcomp(self, dev, mes):
        """Calibrate the solar comparator."""
        j35 = dev['j35']
        dev['dcs_solar'].output(13.0, True, delay=1.0)
        j35['SOLAR'] = True
        j35['SOLAR_STATUS'] = False
        solar_trip = mes['ramp_solar_pre']().reading1
        result = (solar_trip == self.limits['SolarCutoff'])
        if not result:
            low, high = self.limits['SolarCutoff'].limit
            if solar_trip < low:
                j35['SOLAR_OFFSET'] = 2     # Increase cut-off voltage
            if solar_trip > high:
                j35['SOLAR_OFFSET'] = 1     # Decrease cut-off voltage
            j35['NVWRITE'] = True
            # Check the setting after adjustment
            j35['SOLAR_STATUS'] = False
            solar_trip = mes['ramp_solar']().reading1
            result = (solar_trip == self.limits['SolarCutoff'])
        mes['detectcal'].sensor.store(result)
        mes['detectcal']()
        j35['SOLAR'] = False
        dev['dcs_solar'].output(0.0, False)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        j35 = dev['j35']
        dev['acsource'].output(voltage=self.cfg.ac_volt, output=True)
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
        output_count = self.cfg.output_count
        dev['dcl_out'].binary(
            1.0, output_count * self.cfg.load_per_output, 5.0)
        for load in range(output_count):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['arm_loads'][load](timeout=5)
        # Calibrate current reading
        j35['BUS_ICAL'] = output_count * self.cfg.load_per_output
        j35['NVWRITE'] = True
        dev['dcl_bat'].output(self.cfg.batt_current, True)
        self.measure(('dmm_vbatload', 'arm_battI', ), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        j35 = dev['j35']
        ocp_actual = mes['ramp_ocp_pre']().reading1
        # Adjust current setpoint
        j35['OCP_CAL'] = round(
            j35.ocp_cal() * ocp_actual / self.cfg.ocp_set)
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

    sw_version = None   # ARM software version

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
            os.path.join(folder, 'j35_{0}.bin'.format(self.sw_version)),
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

    output_count = None
    load_per_output = None

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
        self['arm_loads'] = []
        for i in range(self.output_count):
            sen = share.console.Sensor(j35, 'LOAD_{0}'.format(i + 1))
            self['arm_loads'].append(sen)
        load_current = self.output_count * self.load_per_output
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
            start=low - 0.1,
            stop=high + 0.1,
            step=0.05)


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
            ('arm_swver', 'SwVer', 'arm_swver', 'Unit software version'),
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
            ('TunnelSwVer', 'SwVer', 'TunnelSwVer', 'Unit software version'),
            ))
        # Generate load current measurements
        loads = []
        for sen in self.sensors['arm_loads']:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        self['arm_loads'] = loads
