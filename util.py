import hashlib
from flask import request

def hash_ip():
    try:
        ip_address = request.headers['X-Real-IP']
    except:
        ip_address = '127.0.0.1'
    # Convert IP address to bytes
    ip_bytes = ip_address.encode('utf-8')

    # Calculate SHA-256 hash
    hashed_ip = hashlib.sha256(ip_bytes).hexdigest()

    return hashed_ip

import subprocess

def get_build_hash():
    hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'])[:6].decode()
    return hash

build_hash = get_build_hash()
print('build hash', build_hash)