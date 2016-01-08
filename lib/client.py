#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import logging
from . import protocol

if sys.version_info.major == 3:
    from xmlrpc.client import ServerProxy
else:
    from xmlrpclib import ServerProxy


class Client(object):
    def __init__(self, host, port):
        self._logger = logging.getLogger(__name__)
        self._server_url = 'http://%s:%d' % (host, port)
        self._server = ServerProxy(self._server_url)

    def run(self):
        self._logger.info('Connecting to URL %s ...',
                          self._server_url)
        stopped = False
        while not stopped:
            try:
                print(self._server.get_rotation())
                time.sleep(1)
            except KeyboardInterrupt:
                self._logger.info("Got a keyboard interrupt!")
                stopped = True
            except Exception:
                self._logger.warning("Error occured during execution!",
                                     exc_info=True)
                stopped = True
        self._logger.info("Client exited.")


class AuthClient(Client):
    def __init__(self, sensor_instance, *args, **kwargs):
        Client.__init__(self, *args, **kwargs)
        self._sensor = sensor_instance

    def run(self):
        self._logger.info('Connecting to URL %s ...',
                          self._server_url)
        stopped = False
        while not stopped:
            try:
                rotation = self._sensor.get_rotation()
                if(self.authenticate(rotation)):
                    stopped = True
                else:
                    time.sleep(1)
            except KeyboardInterrupt:
                self._logger.info("Got a keyboard interrupt!")
                stopped = True
            except Exception:
                self._logger.warning("Error occured during execution!",
                                     exc_info=True)
                stopped = True
        self._logger.info("Client exited.")

    def authenticate(self, client_rotation):
        client_salt = protocol.get_salt()
        client_hash = protocol.hash_rotation(client_rotation, client_salt)

        self._logger.debug('client_rotation: %r', client_rotation)
        self._logger.debug('client_salt: %r', client_salt)
        self._logger.debug('client_hash: %r', client_hash)

        (nonce, server_hash) = self._server.exchange_hashes(client_hash)

        self._logger.debug('nonce: %r', nonce)
        self._logger.debug('server_hash: %r', server_hash)

        (code, message) = self._server.compare_values(nonce, client_salt)
        if code != 0:
            self._logger.error('Authentication failed: %s', message)
        else:
            server_salt = message
            server_hash2 = protocol.hash_rotation(client_rotation, server_salt,
                                                  nonce=nonce)
            self._logger.debug('server_salt: %r', server_salt)
            self._logger.debug('server_hash2: %r', server_hash2)
            if server_hash2 == server_hash:
                self._logger.info('Authentication succeeded!')
                return True
            else:
                self._logger.error('Authentication failed: %s',
                                   'client hash mismatch')
        return False
