#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""RVSWT101 Arduino console driver."""

import share


class Arduino(share.console.Arduino):

    """Communications to RVSWT101 Arduino console."""

    cmd_data = {
        "DEBUG": share.console.parameter.String(
            "DEBUG_ON", writeable=True, write_format="{1}", read_format="{0}"
        ),
        "QUIET": share.console.parameter.String(
            "DEBUG_OFF", writeable=True, write_format="{1}", read_format="{0}"
        ),
        # Actuator commands
        "RETRACT_ACTUATORS": share.console.parameter.String(
            "ACTU_NONE", writeable=True, write_format="{1}", read_format="{0}"
        ),
        "EJECT_DUT": share.console.parameter.String(
            "ACTU_EJECT", writeable=True, write_format="{1}", read_format="{0}"
        ),
        "EXERCISE": share.console.parameter.String(
            "EXERCISE", writeable=True, write_format="{1}", read_format="{0}"
        ),
        # 4 or 6 button configuration
        "4BUTTON_MODEL": share.console.parameter.String(
            "4BUTTON", writeable=True, write_format="{1}", read_format="{0}"
        ),
        "6BUTTON_MODEL": share.console.parameter.String(
            "6BUTTON", writeable=True, write_format="{1}", read_format="{0}"
        ),
        # UUT detection
        "UUT": share.console.parameter.String(
            "UUT", writeable=True, write_format="{1}", read_format="{0}"
        ),
    }
    # Build all 6 PRESS_BUTTON and RELEASE_BUTTON actuator commands
    for button in range(1, 7):
        commands = (
            ("PRESS_BUTTON_{0}".format(button), "ACTU{0};1".format(button)),
            ("RELEASE_BUTTON_{0}".format(button), "ACTU{0};0".format(button)),
        )
        for test_cmd, arduino_cmd in commands:
            cmd_data[test_cmd] = share.console.parameter.String(
                arduino_cmd, writeable=True, write_format="{1}", read_format="{0}"
            )

    def exercise_actuators(self):
        """Exercise routine all actuators.

        If UUT is in place, routine will be cancelled

        """
        if not self.check_uut_in_place():
            self["EXERCISE"]

    def check_uut_in_place(self):
        """Ask arduino if a UUT is in place"""
        return int(self["UUT"])

    def set_state(self, button_count):
        """Set to 4 or 6 button mode"""
        command = {
            4: "4BUTTON_MODEL",
            6: "6BUTTON_MODEL",
        }[button_count]
        self[command]

    def eject_uut(self):
        """Eject the UUT from testing postion."""
        self["EJECT_DUT"]

    def retract_all(self):
        """Retract all button actuators."""
        self["RETRACT_ACTUATORS"]
