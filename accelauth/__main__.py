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
    parser.add_argument('--host', metavar='HOST', type=str,
                        action='store', help='Server IP', default='localhost')
    parser.add_argument('--port', metavar='PORT', type=int,
                        action='store', help='Server port', default=9876)
    parser.add_argument('--auth', action='store_true',
                        help='Use auth protocol')
    parser.add_argument('--bus', metavar='BUS', type=int,
                        action='store', help='SMBus ID', default=1)
    parser.add_argument('--offset', action='store', type=int, nargs=3,
                        metavar=('X', 'Y', 'Z'), default=(0, 0, 0),
                        help='Sensor offset')
    parser.add_argument('--no-quantization', action='store_true',
                        help='Disable Quantization')
    parser.add_argument('--demo', action='store_true', help='Use demo sensor')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--client', action='store_true', help='Run as client',
                      default=True)
    mode.add_argument('--server', action='store_true', help='Run as server')
    mode.add_argument('--test-sensor', action='store_true',
                      help='Test the sensor by printing the values')
    p_args = parser.parse_args(args)

    logging.basicConfig(level=logging.DEBUG if p_args.debug else logging.INFO)

    print('Demo sensor: %s' % ('Yes' if p_args.demo else
                               'No (SMBus ID %d)' % p_args.bus))

    sensor_class = sensor.DemoSensor if p_args.demo else sensor.Accelerometer
    sensor_obj = sensor_class(p_args.bus, offset=p_args.offset,
                              quantize=not p_args.no_quantization)

    if p_args.test_sensor:
        sensor_obj.print_values()
        return

    print('Mode: %s' % ('Server' if p_args.server else 'Client'))
    print('Host: %s' % p_args.host)
    print('Port: %d' % p_args.port)
    print('Auth: %s' % ('Yes' if p_args.auth else 'No'))

    if p_args.server:
        classobj = (server.AuthServer if p_args.auth else server.SimpleServer)
        args = (sensor_obj, p_args.host, p_args.port)
    elif p_args.client:
        classobj = client.AuthClient if p_args.auth else client.Client
        args = (sensor_obj, p_args.host, p_args.port)

    obj = classobj(*args)
    obj.run()


if __name__ == '__main__':
    main()
