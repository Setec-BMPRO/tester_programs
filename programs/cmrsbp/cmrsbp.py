#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility Server - CMR Listener.

Listens to serial traffic from a CMR-SBP.
This is traffic from the PIC, via the SMBus to RS232 converter

Here is a sample CMR transmission from CMR-SBP-8-D-NiMH:
#BATTERY MODE,24576
#TEMPERATURE,297.0
#VOLTAGE,13.710
#CURRENT,0.013
#REL STATE OF CHARGE,100
#ABS STATE OF CHARGE,104
#REMAINING CAPACITY,8283
#FULL CHARGE CAPACITY,8283
#CHARGING CURRENT,0.400
#CHARGING VOLTAGE,16.000
#BATTERY STATUS,224
#CYCLE COUNT,1
#PACK STATUS AND CONFIG,-24416
#FULL PACK READING,790
#HALF CELL READING,397
#SENSE RESISTOR READING,66
#CHARGE INPUT READING,1
#ROTARY SWITCH READING,256
#SERIAL NUMBER,949

"""

import sys
import re
import threading
import queue
import logging
import share


class CmrSbp():

    """CMR Monitor."""

    _datamap = {
        'BATTERY MODE':             (0, int),
        'TEMPERATURE':              (0.0, float),
        'VOLTAGE':                  (0.0, float),
        'CURRENT':                  (0.0, float),
        'REL STATE OF CHARGE':      (0, int),
        'ABS STATE OF CHARGE':      (0, int),
        'REMAINING CAPACITY':       (0, int),
        'FULL CHARGE CAPACITY':     (0, int),
        'CHARGING CURRENT':         (0.0, float),
        'CHARGING VOLTAGE':         (0.0, float),
        'BATTERY STATUS':           (0, int),
        'CYCLE COUNT':              (0, int),
        'PACK STATUS AND CONFIG':   (0, int),
        'FULL PACK READING':        (0, int),
        'HALF CELL READING':        (0, int),
        'SENSE RESISTOR READING':   (0, int),
        'CHARGE INPUT READING':     (0, int),
        'ROTARY SWITCH READING':    (0, int),
        'SERIAL NUMBER':            (0, int),
        }

    # RegExp object to match the CMR data lines
    _regexp = re.compile('^#([A-Z ]+),([0-9\.\-]+)$')

    def __init__(self, port, data_timeout=1.0):
        """Define our data, and start the worker.

        @param port The open serial port to read from
        @param data_timeout Timeout for received CMR-SBP data

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.port = port
        self.ResultQ = queue.Queue()
        self._evt_read = threading.Event()
        self._evt_close = threading.Event()
        self._worker = threading.Thread(
            target=self.worker, name='ListenerThread', args=(data_timeout, ))
        self._worker.start()

    def _scan_line(self, line, tdata):
        """Scan a line, looking for data.

        @return Key, if found, or None

        """
        self._logger.debug('Line %s', line)
        match = self._regexp.match(line)
        if match:
            key, val = match.groups()
            datatype = self._datamap[key][1]
            tdata[key] = datatype(val)
        else:
            key = None
        return key

    def worker(self, data_timeout):
        """Worker to listen to a CMR."""
        self._logger.info('Started')
        err = ''
        run = False
        try:
            self.port.flushInput()
            data_template = {}
            for parameter in iter(self._datamap):
                data_template[parameter] = self._datamap[parameter][0]
            tdata = share.TimedStore(data_template, data_timeout)
            run = True
        except Exception:
            err = ' '.join(
                ('_cmr Error:',
                 str(sys.exc_info()[0]),
                 str(sys.exc_info()[1])))
            self._logger.warning(err)
        buf = ''
        state = 0
        # Data reader states:
        #  0 = idle
        #  3 = waiting for data start
        #  2 = waiting for data end
        #  1 = data ready
        timeup = threading.Event()
        while run:
            rawdata = self.port.read(512).decode(errors='ignore')
            buf += rawdata.replace('\r', '')
            pos = buf.find('\n')
            while pos >= 0:
                line, buf = buf[:pos], buf[pos + 1:]
                if len(line) > 0:
                    key = self._scan_line(line, tdata)
                    if state == 3 and key == 'BATTERY MODE':
                        self._logger.debug('Start data block')
                        state = 2
                    if state == 2 and key == 'SERIAL NUMBER':
                        self._logger.debug('End data block')
                        state = 1
                pos = buf.find('\n')
            if self._evt_read.is_set():
                self._evt_read.clear()
                self._logger.debug('Starting data read')
                state = 3
                timeup.clear()
                tmr = threading.Timer(20.0, timeup.set)
                tmr.start()
            if self._evt_close.is_set():
                run = False
                if state > 0:
                    tmr.cancel()
                    tmr.join()
                continue
            if state == 1:
                tmr.cancel()
                state = 0
                self._logger.debug('Data read completed')
                self.ResultQ.put(tdata.data)    # this will be valid data
            if state > 0 and timeup.is_set():
                state = 0
                self._logger.debug('Data read timeout')
                self.ResultQ.put(tdata.data)    # this will be empty data
        try:
            tdata.cancel()
        except Exception:
            pass
        self._logger.info('Finished!')

    def read(self):
        """Return status data.

        The worker thread will send data in response to a 'READ' event.

        """
        self._logger.debug('Read')
        self._evt_read.set()
        return self.ResultQ.get()

    def close(self):
        """Signal the worker thread to shutdown.

        The worker thread will shut down in response to a 'CLOSE' event.

        """
        self._logger.debug('Close')
        self._evt_close.set()
        self._worker.join()
        self.port.close()
