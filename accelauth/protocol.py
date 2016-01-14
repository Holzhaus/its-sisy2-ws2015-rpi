#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import hashlib
import json
import random
from Crypto import Random
from Crypto.Protocol import KDF
from Crypto.Cipher import AES


def bchr(s):
    if sys.version_info.major == 3:
        return bytes([s])
    else:
        return chr(s)


def bord(s):
    if sys.version_info.major == 3:
        return s
    else:
        return ord(s)


def hash_rotation(rotation, salt, nonce=None):
    m = hashlib.sha1()
    m.update(str(salt).encode('utf-8'))
    if nonce is not None:
        m.update(str(nonce).encode('utf-8'))
    m.update(json.dumps(rotation).encode('utf-8'))
    return m.hexdigest()


def rotation_to_key(rotation):
    passphrase = json.dumps(rotation).encode('utf-8')
    salt = ''.encode('utf-8')  # We're lazy
    return KDF.PBKDF2(passphrase, salt, dkLen=32)


def get_aes(rotation, iv):
    key = rotation_to_key(rotation)
    return AES.new(key, AES.MODE_OFB, iv)


def encrypt(rotation, plaintext):
    padded_plaintext = pad(plaintext.encode('utf-8'), 16)
    rndfile = Random.new()
    iv = rndfile.read(16)
    aes = get_aes(rotation, iv)
    return (aes.encrypt(padded_plaintext), iv)


def decrypt(rotation, ciphertext, iv):
    aes = get_aes(rotation, iv)
    padded_plaintext = aes.decrypt(ciphertext)
    return unpad(padded_plaintext, 16).decode('utf-8')


def pad(data, blocksize):
    padding_len = blocksize-(len(data) % blocksize)
    padding = bchr(padding_len)*padding_len
    return (data + padding)


def unpad(data, blocksize):
    padding_len = bord(data[-1])
    return data[:-padding_len]


def nonce_generator():
    i = 0
    while True:
        yield i
        i += 1


def get_salt():
    return random.random()
