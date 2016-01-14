#!/usr/bin/env python
# -*- coding: utf-8 -*-
import smbus
import time


def quantize(value, old_max, new_max, ndigits=0):
    new_value = float(value)/float(old_max)*float(new_max)
    rounded = round(new_value, ndigits)
    return int(rounded) if ndigits == 0 else rounded


class Axis(object):
    X = 0x06
    Y = 0x07
    Z = 0x08


class DemoSensor(object):
    def __init__(self, *args, **kwargs):
        pass

    def get_rotation(self):
        return (123, 45, 67)

    def print_values(self):
        print('X   Y   Z')
        print('--- --- ---')
        while True:
            print('%3d %3d %3d' % self.get_rotation())
            time.sleep(0.5)


class Accelerometer(DemoSensor):
    def __init__(self, bus):
        self.bus = smbus.SMBus(bus)
        self.calibrate()

    def calibrate(self):
        # Setup mode
        self.bus.write_byte_data(0x1D, 0x16, 0x55)

        # Calibrate
        self.bus.write_byte_data(0x1D, 0x10, 0)
        self.bus.write_byte_data(0x1D, 0x11, 0)
        self.bus.write_byte_data(0x1D, 0x12, 0)
        self.bus.write_byte_data(0x1D, 0x13, 0)
        self.bus.write_byte_data(0x1D, 0x14, 0)
        self.bus.write_byte_data(0x1D, 0x15, 0)

    def get_axis(self, axis):
        value = self.bus.read_byte_data(0x1D, axis)
        return quantize(value, 255, 100)

    def get_rotation(self):
        '''
        Returns the rotation as a tuple in the form (x, y, z).
        '''
        x = self.get_axis(Axis.X)
        y = self.get_axis(Axis.Y)
        z = self.get_axis(Axis.Z)
        return (x, y, z)
