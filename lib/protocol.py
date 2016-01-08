#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import json
import random


def hash_rotation(rotation, salt, nonce=None):
    m = hashlib.sha1()
    m.update(str(salt).encode('utf-8'))
    if nonce is not None:
        m.update(str(nonce).encode('utf-8'))
    m.update(json.dumps(rotation).encode('utf-8'))
    return m.hexdigest()


def nonce_generator():
    i = 0
    while True:
        yield i
        i += 1


def get_salt():
    return random.random()
