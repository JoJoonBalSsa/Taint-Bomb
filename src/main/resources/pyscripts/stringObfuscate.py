import os
import hashlib
from functools import reduce

def key_schedule(key, rounds):
    schedule = [key]
    for i in range(1, rounds):
        new_key = hashlib.sha256(schedule[-1]).digest()
        schedule.append(new_key)
    return schedule

def feistel_network(block, round_key):
    left, right = block[:8], block[8:]
    f_result = bytes(a ^ b for a, b in zip(right, round_key[:8]))
    new_right = bytes(a ^ b for a, b in zip(left, f_result))
    return right + new_right

def encrypt(data, key, rounds=16):
    key_sched = key_schedule(key, rounds)
    encrypted = bytearray()
    for i in range(0, len(data), 16):
        block = data[i:i+16]
        if len(block) < 16:
            block = block.ljust(16, b'\x00')
        for round_key in key_sched:
            block = feistel_network(block, round_key)
        encrypted.extend(block)
    return bytes(encrypted)

def decrypt(data, key, rounds=16):
    key_sched = key_schedule(key, rounds)
    decrypted = bytearray()
    for i in range(0, len(data), 16):
        block = data[i:i+16]
        for round_key in reversed(key_sched):
            block = inverse_feistel_network(block, round_key)
        decrypted.extend(block)
    return bytes(decrypted).rstrip(b'\x00')

def inverse_feistel_network(block, round_key):
    left, right = block[:8], block[8:]
    f_result = bytes(a ^ b for a, b in zip(left, round_key[:8]))
    new_left = bytes(a ^ b for a, b in zip(right, f_result))
    return new_left + left

# 테스트
key = os.urandom(16)
plaintext = b'This is a test message. It is longer than 16 bytes.'
encrypted = encrypt(plaintext, key)
print("Encrypted:", encrypted)
decrypted = decrypt(encrypted, key)
print("Decrypted:", decrypted)
print("Decrypted (as text):", decrypted.decode('utf-8'))