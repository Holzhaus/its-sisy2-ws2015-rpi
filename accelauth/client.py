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
    raw_input = input
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
                key = self.key_agreement(rotation)
                if key is not None:
                    self.exchange_messages(key)
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

    def key_agreement(self, secret):
        self._logger.info('Trying to authenticate...')
        self._logger.debug('secret = %r', secret)

        # Generate challenge cc and send to server
        self._logger.info('Generating client challenge...')
        cc = protocol.get_random_bytes()
        self._logger.debug('cc = %r', cc)

        self._logger.info('Sendig client challenge to server...')
        sc, sr = (self._server.start_challenge_response(Binary(cc)))
        sc = sc.data
        self._logger.info('Received server challenge/response...')
        self._logger.debug('sc = %r', sc)

        if cc == sc:
            self._logger.warning('Both challenges are the same, aborting...')
            return

        # Check if server response is valid
        self._logger.info('Checking if server response is valid...')
        sr_expected = protocol.generate_response(sc, cc, secret)
        self._logger.debug('sr1 = %r', sr)
        self._logger.debug('sr2 = %r (expected)', sr_expected)

        if sr == sr_expected:
            # Server response is valid, we'll send him the client response
            self._logger.info('Server response is valid!')
            cr = protocol.generate_response(cc, sc, secret)
        else:
            # Server response is invalid, we'll send bogus to the server
            self._logger.warning('Server response is invalid!')
            cr = protocol.generate_response(protocol.get_random_bytes())
        self._logger.debug('cr = %r', cr)

        self._logger.info('Sending client response....')
        self._server.finish_challenge_response(cr)

        if sr == sr_expected:
            self._logger.info('Generating key...')
            key = protocol.generate_key(secret, cc, sc)
            self._logger.info('Key generated!')
            self._logger.debug('key = %r', key)
            return key
        else:
            return None

    def exchange_messages(self, key):
        print("Type 'logout' to end conversation.")
        stopped = False
        while not stopped:
            plaintext = raw_input('YOU: ')
            if plaintext.lower() == 'logout':
                stopped = True

            # Encrypt our message
            iv, ciphertext = protocol.encrypt(key, plaintext)
            self._logger.debug('iv = %r', iv)
            self._logger.debug('ciphertext = %r', ciphertext)

            # Send it to the server
            self._logger.info('Sending message to server...')
            s_iv, s_ciphertext = (
                x.data if isinstance(x, Binary) else x
                for x in self._server.send_message(
                    Binary(iv), Binary(ciphertext)))

            # Decrypt the server's message
            self._logger.debug('s_iv = %r', s_iv)
            self._logger.debug('s_ciphertext = %r', s_ciphertext)
            s_message = protocol.decrypt(key, s_iv, s_ciphertext)
            print('SERVER: %s' % s_message)
