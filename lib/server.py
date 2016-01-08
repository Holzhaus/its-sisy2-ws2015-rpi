#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
from . import protocol

if sys.version_info.major == 3:
    from xmlrpc.server import SimpleXMLRPCServer
    from xmlrpc.server import SimpleXMLRPCRequestHandler
    from xmlrpc.client import Binary
else:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
    from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
    from xmlrpclib import Binary


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class Server(SimpleXMLRPCServer):
    def __init__(self, sensor_instance, server_address, server_port):
        self._logger = logging.getLogger()
        self._server_address = server_address
        self._server_port = server_port

        SimpleXMLRPCServer.__init__(
            self,
            (self._server_address, self._server_port),
            requestHandler=RequestHandler,
            logRequests=False)

        self.register_introspection_functions()

        self._sensor = sensor_instance


class SimpleServer(Server):
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)

        self.register_function(self._sensor.get_rotation, 'get_rotation')

    def run(self):
        self._logger.info('Started listening on %s:%d ...',
                          self._server_address, self._server_port)
        stopped = False
        while not stopped:
            try:
                self.handle_request()
            except KeyboardInterrupt:
                self._logger.info("Got a keyboard interrupt!")
                stopped = True
            except Exception:
                self._logger.warning("Error occured during execution!",
                                     exc_info=True)
                stopped = True
        self._logger.info("Server exited.")


class AuthServer(Server):
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self._authdata = {}
        self._authenticated = None
        self._nonces = protocol.nonce_generator()

        self.register_function(self.exchange_hashes, 'exchange_hashes')
        self.register_function(self.compare_values, 'compare_values')
        self.register_function(self.communicate, 'communicate')

    def exchange_hashes(self, client_hash):
        nonce = next(self._nonces)
        self._logger.debug('Exchanging hashes... (nonce %r)', nonce)

        # Get current rotation and hash it
        server_rotation = self._sensor.get_rotation()
        server_salt = protocol.get_salt()
        server_hash = protocol.hash_rotation(server_rotation, server_salt,
                                             nonce=nonce)

        self._logger.debug('server_rotation: %r', server_rotation)
        self._logger.debug('server_salt: %r', server_salt)
        self._logger.debug('server_hash: %r', server_hash)

        # Save server salt and hashed client rotation
        self._authdata[nonce] = (server_rotation, server_salt, client_hash)

        # return our hash
        return (nonce, server_hash)

    def compare_values(self, nonce, client_salt):
        self._logger.debug('Comparing values... (nonce %r)', nonce)
        try:
            data = self._authdata[nonce]
            del self._authdata[nonce]
        except KeyError:
            self._logger.warning('Got invalid nonce: %r', nonce)
            return (1, 'nonce invalid')
        (server_rotation, server_salt, client_hash) = data

        self._logger.debug('server_rotation: %r', server_rotation)
        self._logger.debug('server_salt: %r', server_salt)
        self._logger.debug('client_hash: %r', client_hash)

        client_hash2 = protocol.hash_rotation(server_rotation, client_salt)
        self._logger.debug('client_hash2: %r', client_hash2)

        if client_hash != client_hash2:
            self._logger.warning('Server hash mismatch')
            return (1, 'server hash mismatch')
        else:
            self._logger.warning('Client authenticated! (%r)', server_rotation)
            self._authenticated = server_rotation
            return (0, server_salt)

    def communicate(self, client_iv, client_ciphertext):
        client_iv = client_iv.data
        client_ciphertext = client_ciphertext.data

        self._logger.debug('client_message (encrypted): %r', client_ciphertext)
        self._logger.debug('client_iv: %r', client_iv)

        if self._authenticated is None:
            self._logger.warning('Unauthorized connection attempt!')
            return ('', 'not authenticated')
        server_rotation = self._authenticated
        self._authenticated = None

        self._logger.info("Authenticated client has sent a message")

        client_plaintext = protocol.decrypt(
            server_rotation, client_ciphertext, client_iv)

        self._logger.info("client_message (plain): %s", client_plaintext)

        server_plaintext = 'This is the server\'s answer!'

        self._logger.info("server_message (plain): %s", server_plaintext)

        server_ciphertext, server_iv = protocol.encrypt(
            server_rotation, server_plaintext)

        self._logger.debug('server_iv: %r', server_iv)
        self._logger.debug('server_message (encrypted): %r', server_ciphertext)

        return (Binary(server_ciphertext), Binary(server_iv))

    def run(self):
        self._logger.info('Started listening on %s:%d ...',
                          self._server_address, self._server_port)
        stopped = False
        while not stopped:
            try:
                self.handle_request()
            except KeyboardInterrupt:
                self._logger.info("Got a keyboard interrupt!")
                stopped = True
            except Exception:
                self._logger.warning("Error occured during execution!",
                                     exc_info=True)
                stopped = True
        self._logger.info("Server exited.")
