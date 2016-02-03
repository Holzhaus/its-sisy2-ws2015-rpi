#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging
from lib import sensor
from lib import server
from lib import client

parser = argparse.ArgumentParser(
    description='SiSy2 Gyro Project',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--debug', action='store_true', help='Show debug messages')
parser.add_argument('--host', metavar='HOST', nargs=1,
                    action='store', help='Server IP', default='localhost')
parser.add_argument('--port', metavar='PORT', type=int, nargs=1,
                    action='store', help='Server port', default=9876)
parser.add_argument('--auth', action='store_true', help='Use auth protocol')
parser.add_argument('--bus', metavar='BUS', type=int, nargs=1,
                    action='store', help='SMBus ID', default=1)
parser.add_argument('--offset', action='store', type=int, nargs=3,
                    metavar=('X', 'Y', 'Z'), help='Sensor offset')
parser.add_argument('--no-quantization', action='store_true',
                    help='Disable Quantization')
parser.add_argument('--demo', action='store_true', help='Use demo sensor')
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--client', action='store_true', help='Run as client',
                  default=True)
mode.add_argument('--server', action='store_true', help='Run as server')
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

print('Mode: %s' % ('Server' if args.server else 'Client'))
print('Host: %s' % args.host)
print('Port: %d' % args.port)

if args.server:
    sensor_instance = sensor.get_sensor(args.bus, is_demo=args.demo)
    server_class = server.AuthServer if args.auth else server.SimpleServer
    server_instance = server_class(sensor_instance, args.host, args.port)
    server_instance.run()
elif args.client:
    if args.auth:
        sensor_instance = sensor.get_sensor(args.bus, is_demo=args.demo)
        client_instance = client.AuthClient(
            sensor_instance, args.host, args.port)
    else:
        client_instance = client.Client(args.host, args.port)
    client_instance.run()
