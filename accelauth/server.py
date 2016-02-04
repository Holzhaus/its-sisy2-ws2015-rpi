#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
from . import protocol
import xml.etree.ElementTree as etree

if sys.version_info.major == 3:
    from xmlrpc.server import SimpleXMLRPCServer
    from xmlrpc.server import SimpleXMLRPCRequestHandler
    from xmlrpc.client import Binary
else:
    from SimpleXMLRPCServer import SimpleXMLRPCServer
    from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
    from xmlrpclib import Binary


class UidRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

    def __init__(self, req, addr, server):
        self.logger = logging.getLogger('IpRequestHandler')
        self.uid = addr[0]  # Client's IP address
        SimpleXMLRPCRequestHandler.__init__(self, req, addr, server)

    def decode_request_content(self, content):
        """
        We're overwriting this method in order to insert a client Identifier
        (IP address) as first parameter of the method call. That way we know
        which client we're dealing with in the actual server methods.
        """
        xml = SimpleXMLRPCRequestHandler.decode_request_content(self, content)
        root = etree.fromstring(xml)
        if root.tag != 'methodCall':
            return xml

        # Insert new param containing client_id as first parameter
        el_params = root.find('params')
        el_param = etree.Element('param')
        el_value = etree.SubElement(el_param, 'value')
        el_type = etree.SubElement(el_value, 'string')
        el_type.text = self.uid
        el_params.insert(0, el_param)

        xml = etree.tostring(root, encoding="utf-8", method="xml")
        return xml


class Server(SimpleXMLRPCServer):
    def __init__(self, sensor_instance, server_address, server_port):
        self._logger = logging.getLogger()
        self._server_address = server_address
        self._server_port = server_port

        SimpleXMLRPCServer.__init__(
            self,
            (self._server_address, self._server_port),
            requestHandler=UidRequestHandler,
            logRequests=False)

        self._sensor = sensor_instance


class SimpleServer(Server):
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)

        self.register_function(self.get_rotation, 'get_rotation')

    def get_rotation(self, uid):
        return self._sensor.get_rotation()

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

        self._userdata = {}
        self._userkeys = {}

        self.register_function(
            self.start_challenge_response, 'start_challenge_response')
        self.register_function(
            self.finish_challenge_response, 'finish_challenge_response')
        self.register_function(
            self.send_message, 'send_message')

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

    def start_challenge_response(self, uid, cc):
        self._logger.info('New authentication request from %r!', uid)
        cc = cc.data
        secret = self._sensor.get_rotation()
        self._logger.debug('secret = %r', secret)
        self._logger.debug('cc = %r', cc)

        self._logger.info('Generating server challenge...')
        sc = protocol.get_random_bytes()
        while sc == cc:  # Make sure we don't use the same challenge
            sc = protocol.get_random_bytes()
        self._logger.debug('sc = %r', sc)

        self._logger.info('Generating server response...')
        sr = protocol.generate_response(sc, cc, secret)
        self._logger.debug('sr = %r', sr)

        self._userdata[uid] = (cc, sc, secret)
        self._logger.info('Sending server challenge/response to %r and ' +
                          'wait...', uid)

        return (Binary(sc), sr)

    def finish_challenge_response(self, uid, cr):
        try:
            data = self._userdata.pop(uid)
        except KeyError:
            self._logger.warning('Invalid connection attempt from %r', uid)
        else:
            self._logger.info('Continuing authentication with %r!', uid)
            (cc, sc, secret) = data

            # Check if client response is valid
            self._logger.info('Checking if client response is valid...')
            cr_expected = protocol.generate_response(cc, sc, secret)
            self._logger.debug('cr1 = %r', cr)
            self._logger.debug('cr2 = %r (expected)', cr_expected)

            if cr == cr_expected:
                # Client response is valid, let's generate the key
                self._logger.info('Client response is valid!')
                self._logger.info('Generating key...')
                key = protocol.generate_key(secret, cc, sc)
                self._userkeys[uid] = key
                self._logger.info('Key generated!')
                self._logger.debug('key = %r', key)
            else:
                self._logger.warning('Client response is invalid!')
        return "ok"

    def send_message(self, uid, c_iv, c_ciphertext):
        try:
            key = self._userkeys[uid]
        except KeyError:
            self._logger.warning('No key for decrypting message from %r', uid)
            return
        c_iv, c_ciphertext = (
            x.data if isinstance(x, Binary) else x
            for x in (c_iv, c_ciphertext))

        # Decrypt the client's message
        self._logger.debug('c_iv = %r', c_iv)
        self._logger.debug('c_ciphertext = %r', c_ciphertext)
        c_message = protocol.decrypt(key, c_iv, c_ciphertext)

        print("Received message: %r" % c_message)

        if c_message.lower() == 'logout':
            try:
                del self._userkeys[uid]
            except KeyError:
                pass
            s_message = 'Goodbye!'
        else:
            s_message = 'I received your message, thanks!'

        # Encrypt the server's answer and send it to the client
        self._logger.debug('s_message = %r', s_message)
        s_iv, s_ciphertext = protocol.encrypt(key, s_message)
        self._logger.debug('s_iv = %r', s_iv)
        self._logger.debug('s_ciphertext = %r', s_ciphertext)
        return (Binary(s_iv), Binary(s_ciphertext))
