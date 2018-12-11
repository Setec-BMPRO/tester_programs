#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN9-540 ARM processor console driver."""

import share


class Console(share.console.Base):

    """Communications to GEN9-540 console."""

    # Number of lines in startup banner
    banner_lines = 4
    parameter = share.console.parameter
    cmd_data = {
        'AcFreq': parameter.Float(
            'X-AC-LINE-FREQUENCY', read_format='{0} X?'),
        'AcVolt': parameter.Float(
            'X-AC-LINE-VOLTS', read_format='{0} X?'),
        '5V': parameter.Float(
            'X-RAIL-VOLTAGE-5V', scale=1000, read_format='{0} X?'),
        '12V': parameter.Float(
            'X-RAIL-VOLTAGE-12V', scale=1000, read_format='{0} X?'),
        '24V': parameter.Float(
            'X-RAIL-VOLTAGE-24V', scale=1000, read_format='{0} X?'),
        'SwVer': parameter.String(
            'X-SOFTWARE-VERSION', read_format='{0} X?'),
        'SwBld': parameter.String(
            'X-BUILD-NUMBER', read_format='{0} X?'),
        'CAL_PFC': parameter.Float(
            'CAL-PFC-BUS-VOLTS',
            writeable=True, readable=False,
            scale=1000,
            write_format='{0} {1}', write_expected=1),
        'UNLOCK': parameter.Boolean('$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': parameter.Boolean('NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean('NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'Hz', 'Vrms', 'mV')

    def banner(self):
        """Flush the console banner lines."""
        self.action(None, delay=3, expected=self.banner_lines)

    def initialise(self):
        """First time initialisation of the micro."""
        self.banner()
        self['UNLOCK'] = True
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True

    def calpfc(self, voltage):
        """Issue PFC calibration commands.

        @param voltage Measured PFC bus voltage

        """
        self['CAL_PFC'] = voltage
        self['NVWRITE'] = True
