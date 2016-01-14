# -*- coding: utf-8 -*-
import argparse
import logging
from . import sensor
from . import server
from . import client


def main(args=None):
    parser = argparse.ArgumentParser(
        description='SiSy2 Gyro Project',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', action='store_true',
                        help='Show debug messages')
    parser.add_argument('--host', metavar='HOST', nargs=1,
                        action='store', help='Server IP', default='localhost')
    parser.add_argument('--port', metavar='PORT', type=int, nargs=1,
                        action='store', help='Server port', default=9876)
    parser.add_argument('--auth', action='store_true',
                        help='Use auth protocol')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--client', action='store_true', help='Run as client',
                      default=True)
    mode.add_argument('--server', action='store_true', help='Run as server')
    p_args = parser.parse_args(args)

    logging.basicConfig(level=logging.DEBUG if p_args.debug else logging.INFO)

    print('Mode: %s' % ('Server' if p_args.server else 'Client'))
    print('Host: %s' % p_args.host)
    print('Port: %d' % p_args.port)
    print('Auth: %s' % ('Yes' if p_args.auth else 'No'))

    if p_args.server:
        sensor_instance = sensor.Sensor()
        server_class = (server.AuthServer if p_args.auth
                        else server.SimpleServer)
        server_instance = server_class(sensor_instance,
                                       p_args.host, p_args.port)
        server_instance.run()
    elif p_args.client:
        if p_args.auth:
            sensor_instance = sensor.Sensor()
            client_instance = client.AuthClient(
                sensor_instance, p_args.host, p_args.port)
        else:
            client_instance = client.Client(p_args.host, p_args.port)
        client_instance.run()


if __name__ == '__main__':
    main()
