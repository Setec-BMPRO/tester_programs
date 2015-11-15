#!/usr/bin/env python
"""JSON-RPC Server for Bluetooth.

Provides JSON-RPC access to the PyBlueZ module of Python 2.7
The port number has been arbitrarily chosen.

http://www.jsonrpc.org/specification
    JSON can represent four primitive types
        (Strings, Numbers, Booleans, and Null)
    and two structured types
        (Objects and Arrays)

"""

from __future__ import print_function
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import bluetooth
import time
import threading
import logging.handlers
import traceback

_LISTEN_TO = ('0.0.0.0', 8888)

_CONSOLE_LOG_LEVEL = logging.DEBUG
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'

_EMAIL_SERVER = 'smtp.core.setec.com.au'
_EMAIL_TO = ['testeng@setec.com.au']
_EMAIL_FROM = '"Python Bluetooth Server" <no_reply@setec.com.au>'
_EMAIL_SUBJECT = 'Bluetooth JSON-RPC Server Error'


def _logging_setup():
    """
    Setup the logging system.

    Messages are sent to the stderr console.
    Errors are sent via SMTP.

    """
    # create console handler and set level
    hdlr = logging.StreamHandler()
    hdlr.setLevel(_CONSOLE_LOG_LEVEL)
    # create SMTP handler and set level
    smtp_hdlr = logging.handlers.SMTPHandler(
        _EMAIL_SERVER, _EMAIL_FROM, _EMAIL_TO, _EMAIL_SUBJECT)
    smtp_hdlr.setLevel(logging.ERROR)
    # Log record formatter
    fmtr = logging.Formatter(_LOG_FORMAT)
    # Connect it all together
    hdlr.setFormatter(fmtr)
    smtp_hdlr.setFormatter(fmtr)
    logging.root.addHandler(hdlr)
    logging.root.addHandler(smtp_hdlr)
    logging.root.setLevel(logging.DEBUG)


class MyServer():

    """JSON-RPC Server."""

    def __init__(self, myevent):
        """Create server."""
        self._event = myevent
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))

    def runner(self):
        """Thread target to run the JSON-RPC Server."""
        try:
            self._logger.info('Creating JSON-RPC Server')
            server = SimpleJSONRPCServer(_LISTEN_TO)
            self.server = server
            server.register_function(self.stop)
            server.register_function(self.echo)
            server.register_function(self.scan)
            server.register_function(self.detect)
            self._logger.info('Running on %s', _LISTEN_TO)
            server.serve_forever()
            self._logger.info('Stopped')
        except Exception:
            exc_str = traceback.format_exc()
            logger.error('JSON-RPC Server Exception:\n%s', exc_str)
        finally:
            self.stop()

    def stop(self):
        """
        Stop method.

        Set event to cause a server shutdown.

        """
        self._logger.debug('stopper()')
        self._event.set()

    def echo(self, in_param):
        """Echo the input parameter back to the caller.

        @return Input parameter

        """
        self._logger.debug('echo() called with: %s', repr(in_param))
        return in_param

    def scan(self):
        """Scan for Bluetooth devices.

        @return Nearby devices

        """
        self._logger.debug('scan() called')
        nearby_devices = bluetooth.discover_devices(
            flush_cache=True, lookup_names=True)
        self._logger.debug('Scan results: %s', repr(nearby_devices))
        return nearby_devices

    def detect(self, mac_address):
        """Detect a particular Bluetooth device.

        @return True is MAC address was seen

        """
        self._logger.debug('detect() called for %s', mac_address)
        nearby_devices = self.scan()
        mac_seen = False
        for dev in nearby_devices:
            if mac_address in dev:
                mac_seen = True
        self._logger.debug('detect result: %s', mac_seen)
        return mac_seen


if __name__ == '__main__':
    try:
        _logging_setup()
        logger = logging.getLogger(__name__)
        logger.info('Creating queue')
        myevent = threading.Event()
        logger.info('Creating server')
        myserver = MyServer(myevent)
        logger.info('Starting server')
        mythread = threading.Thread(
            target=myserver.runner, name='ServerThread')
        mythread.start()
        logger.info('Waiting for shutdown event')
        myevent.wait()
        time.sleep(0.1)  # so logger messages don't overlap
        logger.info('Shutting down server')
        myserver.server.shutdown()
        logger.info('JSON-RPC Server stopped')
        mythread.join()
    except Exception:
        exc_str = traceback.format_exc()
        logger.error('JSON-RPC Server Exception:\n%s', exc_str)
