#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import logging

if sys.version_info.major == 3:
    from xmlrpc.client import ServerProxy
else:
    from xmlrpclib import ServerProxy


class Client(object):
    def __init__(self, host, port):
        self._logger = logging.getLogger(__name__)
        self._server_url = 'http://%s:%d' % (host, port)
        self._proxy = ServerProxy(self._server_url)

    def run(self):
        self._logger.info('Connecting to URL %s ...',
                          self._server_url)
        stopped = False
        while not stopped:
            try:
                print(self._proxy.get_rotation())
                time.sleep(1)
            except KeyboardInterrupt:
                self._logger.info("Got a keyboard interrupt!")
                stopped = True
            except Exception:
                self._logger.warning("Error occured during execution!",
                                     exc_info=True)
                stopped = True
        self._logger.info("Client exited.")
