# -*- coding: utf-8 -*-
"""
Protocol overview

             AUTHENTICATION AND KEY AGREEMENT

CLIENT                                            SERVER

01. Generate  challenge cc

        ================ ( cc ) ==============>>

                               02. Generate challenge sc
                            03. sr = H(sc + cc + secret)

        <<=========== ( sr, sc ) ===============

04. check if sr is correct
05. cr =  H(cc + sc + secret)

        ================ ( cr ) ==============>>

                              06. check if cr is correct
                           07. k = KDF(cc + sc + secret)

08. k = KDF(cc + sc + secret)


                       MESSAGING

CLIENT                                            SERVER

09. generate iv1
10. c1 = AES_k(iv1, m1)

        ============== ( iv1, c1 ) ===========>>

                                11. m1 = dec_k(iv1, c1)
                                       12. generate iv2
                                13. c2 = enc_k(iv2, m2)

        <<============ ( iv2, c2 ) =============

14. m2 = dec_k(iv2, c2)

                         [...]
"""

import sys
import hashlib
from Crypto import Random
from Crypto.Protocol import KDF
from Crypto.Cipher import AES


def get_random_bytes(size=16):
    rndfile = Random.new()
    return rndfile.read(size)


def generate_response(*args):
    m = hashlib.sha1()
    for x in args:
        m.update(str(x).encode('utf-8'))
    return m.hexdigest()


def generate_key(secret, *args):
    passphrase = str(secret).encode('utf8')
    salt = b''.join([str(x).encode('utf8') for x in args])
    return KDF.PBKDF2(passphrase, salt, dkLen=32)


def encrypt(key, plaintext):
    iv = get_random_bytes(size=16)
    aes = AES.new(key, AES.MODE_OFB, iv)
    padded_plaintext = pad(plaintext.encode('utf-8'), 16)
    return (iv, aes.encrypt(padded_plaintext))


def decrypt(key, iv, ciphertext):
    aes = AES.new(key, AES.MODE_OFB, iv)
    padded_plaintext = aes.decrypt(ciphertext)
    return unpad(padded_plaintext, 16).decode('utf-8')


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


def pad(data, blocksize):
    padding_len = blocksize-(len(data) % blocksize)
    padding = bchr(padding_len)*padding_len
    return (data + padding)


def unpad(data, blocksize):
    padding_len = bord(data[-1])
    return data[:-padding_len]
