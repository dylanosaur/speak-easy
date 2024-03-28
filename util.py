import hashlib

def hash_ip(ip_address):
    # Convert IP address to bytes
    ip_bytes = ip_address.encode('utf-8')

    # Calculate SHA-256 hash
    hashed_ip = hashlib.sha256(ip_bytes).hexdigest()

    return hashed_ip

import subprocess
build_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'])[:6].decode()
print('build hash', build_hash)