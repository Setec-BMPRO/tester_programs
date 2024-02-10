#!/usr/bin/env python3
# Copyright 2020 SETEC Pty Ltd.
"""IDS-500 Configuration."""


# Software image filenames
pic_hex_mic = "ids_picMic_2.hex"
pic_hex_syn = "ids_picSyn_2.hex"

# LDD absolute error limits in Amps
#   Ellex "SP-LPPSU-05 (Customer Specification Issue 5)":
#       IS_Set (0-5V) to Iout (0-50A):     ±(0.7% + 10mA)
#       Iout (0-50A) to IS_Iout (0-5V):    ±(0.7% +  5mV)  [ 5mV == 50mA ]
#       IS_Set (0-5V) to IS_Iout (0-5V):   <Not specified>
#
# Rev 9+ limits
#   Rev <9 cannot meet the specifications...
ldd_set_out_error_6 = 0.052
ldd_out_mon_error_6 = 0.092
ldd_set_out_error_50 = 0.36
ldd_out_mon_error_50 = 0.40
# Pre-Rev 9 limits
# ldd_set_out_error_6 = 0.07
# ldd_out_mon_error_6 = 0.092
# ldd_set_out_error_50 = 0.7
# ldd_out_mon_error_50 = 0.7
