#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import logging
from operator import sub
from . import protocol

if sys.version_info.major == 3:
    from xmlrpc.client import ServerProxy
    from xmlrpc.client import Binary
else:
    from xmlrpclib import ServerProxy
    from xmlrpclib import Binary


class Client(object):
    def __init__(self, sensor_instance, host, port):
        self._logger = logging.getLogger(__name__)
        self._server_url = 'http://%s:%d' % (host, port)
        self._server = ServerProxy(self._server_url)
        self._sensor = sensor_instance

    def run(self):
        self._logger.info('Connecting to URL %s ...',
                          self._server_url)
        stopped = False
        while not stopped:
            try:
                server_rotation = tuple(self._server.get_rotation())
                client_rotation = tuple(self._sensor.get_rotation())
            except KeyboardInterrupt:
                self._logger.info("Got a keyboard interrupt!")
                stopped = True
            except Exception:
                self._logger.warning("Error occured during execution!",
                                     exc_info=True)
                stopped = True
            else:
                offset = tuple(map(sub, server_rotation, client_rotation))
                print('          X   Y   Z')
                print('Server: %3d %3d %3d' % server_rotation)
                print('Client: %3d %3d %3d' % client_rotation)
                print('Offset: %3d %3d %3d' % offset)
                print('')
                time.sleep(1)
        self._logger.info("Client exited.")


class AuthClient(Client):
    def run(self):
        self._logger.info('Connecting to URL %s ...',
                          self._server_url)
        stopped = False
        while not stopped:
            try:
                rotation = self._sensor.get_rotation()
                if(self.authenticate(rotation)):
                    message = 'This is a secret message from the client.'
                    self.exchange_secret_messages(rotation, message)
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
        self._logger.debug('Trying to authenticate...')
        client_salt = protocol.get_salt()
        client_hash = protocol.hash_rotation(client_rotation, client_salt)

        self._logger.debug('client_rotation: %r', client_rotation)
        self._logger.debug('client_salt: %r', client_salt)
        self._logger.debug('client_hash: %r', client_hash)

        server_hash = self._server.exchange_hashes(client_hash)

        self._logger.debug('server_hash: %r', server_hash)

        (code, message) = self._server.compare_values(client_salt)
        if code != 0:
            self._logger.error('Authentication failed: %s', message)
        else:
            server_salt = message
            server_hash2 = protocol.hash_rotation(client_rotation, server_salt)
            self._logger.debug('server_salt: %r', server_salt)
            self._logger.debug('server_hash2: %r', server_hash2)
            if server_hash2 == server_hash:
                self._logger.info('Authentication succeeded! (%r)',
                                  client_rotation)
                return True
            else:
                self._logger.error('Authentication failed: %s',
                                   'client hash mismatch')
        return False

    def exchange_secret_messages(self, client_rotation, client_plaintext):
        self._logger.debug('Exchanging secret messages...')
        self._logger.info('client_message (plain): %r', client_plaintext)

        client_ciphertext, client_iv = protocol.encrypt(
            client_rotation, client_plaintext)

        self._logger.debug('client_message (encrypted): %r', client_ciphertext)
        self._logger.debug('client_iv: %r', client_iv)

        server_answer = self._server.communicate(
            Binary(client_iv), Binary(client_ciphertext))

        if tuple(server_answer) == ('', 'not authenticated'):
            self._logger.critical('Server says were not authenticated!')
            return

        server_ciphertext = server_answer[0].data
        server_iv = server_answer[1].data

        self._logger.debug('server_iv: %r', server_iv)
        self._logger.debug('server_message (encrypted): %r', server_ciphertext)

        server_plaintext = protocol.decrypt(
            client_rotation, server_ciphertext, server_iv)

        self._logger.info('server_message (plain): %r', server_plaintext)
