#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BP35 Initial Test Program."""

import os
import inspect
import time
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp,
    LimitBetween, LimitDelta, LimitPercent, LimitInteger
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """BP35 Initial Test Program."""

    # ARM software image file
    arm_file = 'bp35_{0}.bin'.format(config.BP35.arm_sw_version)
    # dsPIC software image file
    pic_file = 'bp35sr_{0}.hex'.format(config.BP35.pic_sw_version)
    # Injected Vbat & Vaux
    vbat_in = 12.4
    vaux_in = 13.5
    # PFC settling level
    pfc_stable = 0.05
    # Converter loading
    iload = 28.0
    ibatt = 4.0
    # Other settings
    vac = 240.0
    outputs = 14
    vout_set = 12.8
    ocp_set = 35.0
    # Extra % error in OCP allowed before adjustment
    ocp_adjust_percent = 10.0
    # SR Solar Reg settings
    sr_vset = 13.650
    sr_vset_settle = 0.05
    sr_iset = 30.0
    sr_ical = 10.0
    sr_vin = 20.0
    sr_vin_pre_percent = 6.0
    sr_vin_post_percent = 1.5
    # PM Solar Reg settings
    pm_zero_wait = 30     # Settling delay for zero calibration
    # Common limits
    _common = (
        LimitLow('FixtureLock', 200, doc='Contacts closed'),
        LimitDelta('HwVer8', 4400.0, 250.0, doc='Hardware Rev ≥8'),
        LimitDelta('ACin', vac, 5.0, doc='Injected AC voltage present'),
        LimitBetween('Vpfc', 401.0, 424.0, doc='PFC running'),
        LimitBetween('12Vpri', 11.5, 13.0, doc='Control rail present'),
        LimitBetween('15Vs', 11.5, 13.0, doc='Control rail present'),
        LimitBetween('Vload', 12.0, 12.9, doc='Load output present'),
        LimitLow('VloadOff', 0.5, doc='Load output off'),
        LimitDelta('VbatIn', 12.0, 0.5, doc='Injected Vbatt present'),
        LimitBetween('Vbat', 12.2, 13.0, doc='Vbatt present'),
        LimitDelta('Vaux', 13.4, 0.4, doc='Vaux present'),
        LimitDelta('3V3', 3.30, 0.05, doc='3V3 present'),
        LimitDelta('FanOn', 12.5, 0.5, doc='Fans ON'),
        LimitLow('FanOff', 0.5, doc='Fans OFF'),
        LimitPercent('OCP_pre', ocp_set, 4.0 + ocp_adjust_percent,
            doc='Before adjustment'),
        LimitPercent('OCP', ocp_set, 4.0, doc='After adjustment'),
        LimitLow('InOCP', 11.6, doc='Output voltage in OCP'),
        LimitRegExp(
            'ARM-SwVer', '^{0}$'.format(
                config.BP35.arm_sw_version.replace('.', r'\.')),
            doc='Software version'),
        LimitDelta('ARM-AcV', vac, 10.0, doc='AC voltage'),
        LimitDelta('ARM-AcF', 50.0, 1.0, doc='AC frequency'),
        LimitBetween('ARM-SecT', 8.0, 70.0, doc='Reading ok'),
        LimitDelta('ARM-Vout', 12.45, 0.45),
        LimitBetween('ARM-Fan', 0, 100, doc='Fan running'),
        LimitDelta('ARM-LoadI', 2.1, 0.9, doc='Load current flowing'),
        LimitDelta('ARM-BattI', ibatt, 1.0, doc='Battery current flowing'),
        LimitDelta('ARM-BusI', iload + ibatt, 3.0, doc='Bus current flowing'),
        LimitPercent('ARM-AuxV', vaux_in, percent=2.0, delta=0.3,
            doc='AUX present'),
        LimitBetween('ARM-AuxI', 0.0, 1.5, doc='AUX current flowing'),
        LimitInteger('ARM-RemoteClosed', 1, doc='REMOTE input connected'),
        LimitDelta('CanPwr', vout_set, delta=1.8,
            doc='CAN bus power present'),
        LimitRegExp('CAN_RX', r'^RRQ,32,0', doc='Expected CAN message'),
        LimitInteger('CAN_BIND', 1 << 28, doc='CAN comms established'),
        LimitInteger('Vout_OV', 0, doc='Over-voltage not triggered'),
        )
    # SR Solar specific limits
    _sr_solar = (
        LimitDelta('SolarVcc', 3.3, 0.1, doc='Vcc present'),
        LimitDelta('SolarVin', sr_vin, 0.5, doc='Input present'),
        LimitPercent('VsetPre', sr_vset, 6.0, doc='Vout before calibration'),
        LimitPercent('VsetPost', sr_vset, 1.5, doc='Vout after calibration'),
        LimitPercent('ARM-IoutPre', sr_ical, (9.0, 20.0),
            doc='Iout before calibration'),
        LimitPercent('ARM-IoutPost', sr_ical, 3.0,
            doc='Iout after calibration'),
        LimitPercent('ARM-SolarVin-Pre', sr_vin, sr_vin_pre_percent,
            doc='Vin before calibration'),
        LimitPercent('ARM-SolarVin-Post', sr_vin, sr_vin_post_percent,
            doc='Vin after calibration'),
        LimitInteger('SR-Alive', 1, doc='Detected'),
        LimitInteger('SR-Relay', 1, doc='Input relay ON'),
        LimitInteger('SR-Error', 0, doc='No error'),
        )
    # PM Solar specific limits
    _pm_solar = (
        LimitInteger('PM-Alive', 1, doc='Detected'),
        LimitDelta('ARM-PmSolarIz-Pre', 0, 0.6, doc='Zero reading before cal'),
        LimitDelta('ARM-PmSolarIz-Post', 0, 0.1, doc='Zero reading after cal'),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    #   'Limits': Test limits.
    #   'HwVer': Hardware version data.
    limitdata = {
        'SR': {
            'Limits': _common + _sr_solar,
            'HwVer': config.BP35SR.arm_hw_version,
            },
        'PM': {
            'Limits': _common + _pm_solar,
            'HwVer': config.BP35PM.arm_hw_version,
            },
        'HA': {
            'Limits': _common + _sr_solar,
            'HwVer': config.BP35HA.arm_hw_version,
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        self.config = self.limitdata[self.parameter]
        super().open(
            self.config['Limits'], Devices, Sensors, Measurements)
        self.pm = (self.parameter == 'PM')
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('ProgramPIC', self._step_program_pic, not self.pm),
            TestStep('ProgramARM', self._step_program_arm),
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
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals to power up the ARM.

        """
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self.measure(('dmm_lock', 'hardware8', ), timeout=5)
        dev['dcs_vbat'].output(self.vbat_in, True)
        dev['rla_vbat'].set_on()
        self.measure(('dmm_vbatin', 'dmm_3v3'), timeout=5)

    @share.teststep
    def _step_program_pic(self, dev, mes):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        dev['SR_LowPower'].output(self.sr_vin, output=True)
        mes['dmm_solarvcc'](timeout=5)
        # Start programming in the background
        dev['program_pic'].program_begin()

    @share.teststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        dev['program_arm'].program()
        if not self.pm:
            with tester.PathName('PICcheck'):
                # PIC programming should be finished by now
                dev['program_pic'].program_wait()
                dev['SR_LowPower'].output(0.0)
        # Cold Reset microprocessor for units that were already programmed
        # (Pulsing RESET isn't enough to reconfigure the I/O circuits)
        dcsource, load = dev['dcs_vbat'], dev['dcl_bat']
        dcsource.output(0.0)
        load.output(1.0, delay=0.5)
        load.output(0.0)
        dcsource.output(self.vbat_in)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        if not self.pm:
            dev['SR_LowPower'].output(self.sr_vin)
        bp35 = dev['bp35']
        bp35.open()
        bp35.brand(
            self.config['HwVer'], self.sernum, dev['rla_reset'],
            self.pm, config.BP35.pic_hw_version)
        mes['arm_swver']()
        if self.pm:
            bp35['PM_RELAY'] = False
            time.sleep(0.5)
            bp35['PM_RELAY'] = True
            dev['PmTimer'].start(self.pm_zero_wait)
        bp35.manual_mode(start=True)    # Start the change to manual mode
        bp35['FAN'] = 0

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
        bp35.sr_set(self.sr_vset, self.sr_iset, delay=2)
        bp35['VOUT_OV'] = 2     # Reset OVP Latch because of Solar overshoot
        # Read solar input voltage and patch measurement limits
        sr_vin = mes['dmm_solarvin'](timeout=5).reading1
        mes['arm_sr_vin_pre'].testlimit = (
            LimitPercent(
                'ARM-SolarVin-Pre', sr_vin, self.sr_vin_pre_percent), )
        mes['arm_sr_vin_post'].testlimit = (
            LimitPercent(
                'ARM-SolarVin-Post', sr_vin, self.sr_vin_post_percent), )
        # Check that Solar Reg is error-free, the relay is ON, Vin reads ok
        self.measure(
            ('arm_sr_error', 'arm_sr_relay', 'arm_sr_vin_pre', ),
            timeout=5)
        # Wait for the voltage to settle
        vmeasured = mes['dmm_vsetpre'].stable(self.sr_vset_settle).reading1
        bp35['SR_VCAL'] = vmeasured     # Calibrate output voltage setpoint
        bp35['SR_VIN_CAL'] = sr_vin     # Calibrate input voltage reading
        # Solar sw ver 182 will not change the setpoint until a DIFFERENT
        # voltage setpoint is given...
        bp35.sr_set(self.sr_vset - 0.05, self.sr_iset, delay=0.2)
        bp35.sr_set(self.sr_vset, self.sr_iset, delay=1)
        self.measure(('arm_sr_vin_post', 'dmm_vsetpost', ))
        dev['dcl_bat'].output(self.sr_ical, True)
        mes['arm_ioutpre'](timeout=5)
        bp35['SR_ICAL'] = self.sr_ical       # Calibrate current setpoint
        time.sleep(1)
        mes['arm_ioutpost'](timeout=5)
        dev['dcl_bat'].output(0.0)
        dev['SR_HighPower'].output(False)

    @share.teststep
    def _step_aux(self, dev, mes):
        """Apply Auxiliary input."""
        bp35, source, load = dev['bp35'], dev['dcs_vaux'], dev['dcl_bat']
        source.output(self.vaux_in, output=True)
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
        bp35.manual_mode(vout=self.vout_set, iout=self.ocp_set)
        dev['acsource'].output(voltage=self.vac, output=True)
        self.measure(('dmm_acin', 'dmm_pri12v'), timeout=10)
        bp35.power_on()
        # Wait for PFC overshoot to settle
        mes['dmm_vpfc'].stable(self.pfc_stable)
        mes['arm_vout_ov']()
        # Remove injected Battery voltage
        dev['rla_vbat'].set_off()
        dev['dcs_vbat'].output(0.0, output=False)
        mes['arm_vout_ov']()
        # Is it now running on it's own?
        self.measure(('dmm_3v3', 'dmm_15vs'), timeout=10)
        v_actual = self.measure(('dmm_vbat', ), timeout=10).reading1
        bp35['VSET_CAL'] = v_actual     # Calibrate Vout setting and reading
        bp35['VBUS_CAL'] = v_actual
        bp35['NVWRITE'] = True

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches."""
        bp35 = dev['bp35']
        # All outputs OFF
        bp35.load_set(set_on=True, loads=())
        # A little load on the output.
        dev['dcl_out'].output(1.0, True)
        mes['dmm_vloadoff'](timeout=2)
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
        dev['dcl_out'].binary(1.0, self.iload, 5.0)
        dev['dcl_bat'].output(self.ibatt, output=True)
        self.measure(('dmm_vbat', 'arm_ibat', 'arm_ibus', ), timeout=5)
        bp35['BUS_ICAL'] = self.iload + self.ibatt  # Calibrate current reading
        for load in range(self.outputs):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['arm_loads'][load](timeout=5)
        ocp_actual = mes['ramp_ocp_pre']().reading1
        # Adjust current setpoint
        bp35['OCP_CAL'] = round(bp35.ocp_cal() * ocp_actual / self.ocp_set)
        bp35['NVWRITE'] = True
        mes['ramp_ocp']()
        dev['dcl_out'].output(0.0)
        dev['dcl_bat'].output(0.0)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        self.measure(('dmm_canpwr', 'arm_can_bind', ), timeout=10)
        bp35tunnel = dev['bp35tunnel']
        bp35tunnel.open()
        mes['TunnelSwVer']()
        bp35tunnel.close()


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


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
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
        arm_port = share.fixture.port('027176', 'ARM')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_arm'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, Initial.arm_file), crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # PIC device programmer
        self['program_pic'] = share.programmer.PIC(
            Initial.pic_file, folder, '33FJ16GS402', self['rla_pic'])
        # Serial connection to the BP35 console
        bp35_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bp35_ser.port = arm_port
        # BP35 Console driver
        self['bp35'] = console.DirectConsole(bp35_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.SETECDeviceID.bp35)
        self['bp35tunnel'] = console.TunnelConsole(tunnel)
        # High power source for the SR Solar Regulator
        self['SR_HighPower'] = SrHighPower(self['rla_acsw'], self['acsource'])
        self['PmTimer'] = share.timers.BackgroundTimer()

    def reset(self):
        """Reset instruments."""
        self['bp35'].close()
        self['bp35tunnel'].close()
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
        self['acin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['acin'].doc = 'Across C101'
        self['vpfc'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
        self['vpfc'].doc = 'Voltage on C111'
        self['vload'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['vload'].doc = 'All Load outputs combined'
        self['vbat'] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self['vbat'].doc = 'Battery output'
        self['vset'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['vset'].doc = 'Between TP308,9 and Vout'
        self['pri12v'] = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self['pri12v'].doc = 'Across C213'
        self['o3v3'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self['o3v3'].doc = 'U307 Output'
        self['fan'] = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self['fan'].doc = 'Across C402'
        self['hardware'] = sensor.Res(dmm, high=8, low=4, rng=100000, res=1)
        self['hardware'].doc = 'Across R631'
        self['o15vs'] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self['o15vs'].doc = 'Across C312'
        self['lock'] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self['lock'].doc = 'Microswitch contacts'
        self['solarvcc'] = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self['solarvcc'].doc = 'TP301'
        self['solarvin'] = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001)
        self['solarvin'].doc = 'TP306,7'
        self['canpwr'] = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.01)
        self['canpwr'].doc = 'X303'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bp35_initial', 'msgSnEntry'),
            caption=tester.translate('bp35_initial', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        bp35 = self.devices['bp35']
        bp35tunnel = self.devices['bp35tunnel']
        for name, cmdkey, units in (
                ('arm_acv', 'AC_V', 'Vac'),
                ('arm_acf', 'AC_F', 'Hz'),
                ('arm_sect', 'SEC_T', '°C'),
                ('arm_vout', 'BUS_V', 'V'),
                ('arm_fan', 'FAN', '%'),
                ('arm_canbind', 'CAN_BIND', ''),
                ('arm_ibat', 'BATT_I', 'A'),
                ('arm_ibus', 'BUS_I', 'A'),
                ('arm_vaux', 'AUX_V', 'V'),
                ('arm_iaux', 'AUX_I', 'A'),
                ('arm_vout_ov', 'VOUT_OV', ''),
                ('arm_iout', 'SR_IOUT', 'A'),
                ('arm_remote', 'BATT_SWITCH', ''),
                # SR Solar Regulator
                ('arm_sr_alive', 'SR_ALIVE', '0/1'),
                ('arm_sr_relay', 'SR_RELAY', '0/1'),
                ('arm_sr_error', 'SR_ERROR', ''),
                ('arm_sr_vin', 'SR_VIN', 'V'),
                # PM Solar Regulator
                ('arm_pm_alive', 'PM_ALIVE', '0/1'),
                ('arm_pm_iout', 'PM_IOUT', 'A'),
                ('arm_pm_iout_rev', 'PM_IOUT_REV', '-A'),
            ):
            self[name] = share.console.Sensor(bp35, cmdkey)
            if units:
                self[name].units = units
        self['arm_swver'] = share.console.Sensor(
            bp35, 'SW_VER', rdgtype=sensor.ReadingString)
        self['TunnelSwVer'] = share.console.Sensor(
            bp35tunnel, 'SW_VER', rdgtype=sensor.ReadingString)
        # Generate load current sensors
        loads = []
        for i in range(1, Initial.outputs + 1):
            loads.append(share.console.Sensor(bp35, 'LOAD_{0}'.format(i)))
        self['arm_loads'] = loads
        # Pre-adjust OCP
        low, high = self.limits['OCP_pre'].limit
        self['ocp_pre'] = sensor.Ramp(
            stimulus=self.devices['dcl_bat'],
            sensor=self['vbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - Initial.iload - 1,
            stop=high - Initial.iload + 1,
            step=0.1)
        self['ocp_pre'].units = 'A'
        self['ocp_pre'].on_read = lambda value: value + Initial.iload
        # Post-adjust OCP
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_bat'],
            sensor=self['vbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - Initial.iload - 1,
            stop=high - Initial.iload + 1,
            step=0.1)
        self['ocp'].units = 'A'
        self['ocp'].on_read = lambda value: value + Initial.iload


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('hardware8', 'HwVer8', 'hardware', 'Hardware version'),
            ('dmm_lock', 'FixtureLock', 'lock', 'Fixture lid closed'),
            ('dmm_acin', 'ACin', 'acin', 'AC input voltage'),
            ('dmm_vpfc', 'Vpfc', 'vpfc', 'PFC output voltage'),
            ('dmm_pri12v', '12Vpri', 'pri12v', 'Primary 12V control rail'),
            ('dmm_15vs', '15Vs', 'o15vs', 'Secondary 15V rail'),
            ('dmm_vload', 'Vload', 'vload', 'Outputs on'),
            ('dmm_vloadoff', 'VloadOff', 'vload', 'Outputs off'),
            ('dmm_vbatin', 'VbatIn', 'vbat', 'Injected Vbatt voltage'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Vbatt output voltage'),
            ('dmm_vaux', 'Vaux', 'vbat', 'Vaux output voltage'),
            ('dmm_3v3', '3V3', 'o3v3', '3V3 rail voltage'),
            ('dmm_fanon', 'FanOn', 'fan', 'Fans running'),
            ('dmm_fanoff', 'FanOff', 'fan', 'Fans off'),
            ('ramp_ocp_pre', 'OCP_pre', 'ocp', 'OCP point (pre-cal)'),
            ('ramp_ocp', 'OCP', 'ocp', 'OCP point (post-cal)'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', 'Unit software version'),
            ('arm_acv', 'ARM-AcV', 'arm_acv', 'AC voltage'),
            ('arm_acf', 'ARM-AcF', 'arm_acf', 'AC frequency'),
            ('arm_sect', 'ARM-SecT', 'arm_sect', 'Temperature'),
            ('arm_vout', 'ARM-Vout', 'arm_vout', 'Vbatt'),
            ('arm_fan', 'ARM-Fan', 'arm_fan', 'FAN speed setting'),
            ('dmm_canpwr', 'CanPwr', 'canpwr', 'CAN bus rail voltage'),
            ('arm_can_bind', 'CAN_BIND', 'arm_canbind', 'CAN bound'),
            ('arm_ibat', 'ARM-BattI', 'arm_ibat', 'Battery current'),
            ('arm_ibus', 'ARM-BusI', 'arm_ibus', 'Bus current'),
            ('arm_vaux', 'ARM-AuxV', 'arm_vaux', 'Aux voltage'),
            ('arm_iaux', 'ARM-AuxI', 'arm_iaux', 'Aux current'),
            ('arm_vout_ov', 'Vout_OV', 'arm_vout_ov', 'Vout OVP'),
            ('arm_remote', 'ARM-RemoteClosed', 'arm_remote', 'Remote input'),
            ('TunnelSwVer', 'ARM-SwVer', 'TunnelSwVer', ''),
            ))
        if self.parameter == 'PM':      # PM Solar Regulator
            self.create_from_names((
                ('arm_pm_alive', 'PM-Alive', 'arm_pm_alive',
                    'Solar alive'),
                ('arm_pm_iz_pre', 'ARM-PmSolarIz-Pre', 'arm_pm_iout',
                    'Solar zero current (pre-cal)'),
                ('arm_pm_iz_post', 'ARM-PmSolarIz-Post', 'arm_pm_iout',
                    'Solar zero current (post-cal)'),
                ))
        else:                           # SR Solar Regulator
            self.create_from_names((
                ('dmm_solarvcc', 'SolarVcc', 'solarvcc',
                    'Solar Vcc rrunning'),
                ('dmm_solarvin', 'SolarVin', 'solarvin',
                    'Solar input present'),
                ('arm_sr_alive', 'SR-Alive', 'arm_sr_alive',
                    'Solar alive'),
                ('arm_sr_relay', 'SR-Relay', 'arm_sr_relay',
                    'Solar relay on'),
                ('arm_sr_error', 'SR-Error', 'arm_sr_error',
                    'Solar error flag clear'),
                ('arm_sr_vin_pre', 'ARM-SolarVin-Pre', 'arm_sr_vin',
                    'Solar input voltage (pre-cal)'),
                ('arm_sr_vin_post', 'ARM-SolarVin-Post', 'arm_sr_vin',
                    'Solar input voltage (post-cal)'),
                ('dmm_vsetpre', 'VsetPre', 'vset',
                    'Solar output voltage (pre-cal)'),
                ('dmm_vsetpost', 'VsetPost', 'vset',
                    'Solar output voltage (post-cal)'),
                ('arm_ioutpre', 'ARM-IoutPre', 'arm_iout',
                    'Solar output current (pre-cal)'),
                ('arm_ioutpost', 'ARM-IoutPost', 'arm_iout',
                    'Solar output current (post-cal)'),
                ))
        # Generate load current measurements
        loads = []
        for sen in self.sensors['arm_loads']:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        self['arm_loads'] = loads
