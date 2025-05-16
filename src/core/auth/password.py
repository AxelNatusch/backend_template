"""
Password utilities for secure authentication.
https://docs.python.org/3/library/hashlib.html
"""

import hashlib
import os
import base64
import json

# Default scrypt parameters
DEFAULT_N = 2**14  # CPU/memory cost factor
DEFAULT_R = 8  # Block size
DEFAULT_P = 1  # Parallelization factor
DEFAULT_DKLEN = 32  # Derived key length


def get_password_hash(
    password: str,
    n: int = DEFAULT_N,
    r: int = DEFAULT_R,
    p: int = DEFAULT_P,
    dklen: int = DEFAULT_DKLEN,
) -> str:
    """
    Hash a password using scrypt.

    Args:
        password: Plain text password
        n: CPU/memory cost parameter (must be power of 2)
        r: Block size parameter
        p: Parallelization parameter
        dklen: Derived key length

    Returns:
        Hashed password with salt and parameters (base64 encoded)
    """
    salt = os.urandom(16)
    hash_bytes = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=dklen)

    # Store parameters along with the salt and hash
    params = {"n": n, "r": r, "p": p, "dklen": dklen}

    # Format: base64(json_params + ":" + salt + hash)
    param_string = json.dumps(params).encode("utf-8")
    result = param_string + b":" + salt + hash_bytes
    encoded = base64.b64encode(result).decode("utf-8")

    return encoded


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches hash, False otherwise
    """
    try:
        # Decode the stored hash
        decoded = base64.b64decode(hashed_password.encode("utf-8"))

        # Find the end of the JSON object by counting braces
        json_end = -1
        brace_count = 0
        for i, c in enumerate(decoded):
            if c == ord("{"):
                brace_count += 1
            elif c == ord("}"):
                brace_count -= 1
                if brace_count == 0:
                    json_end = i
                    break

        if json_end < 0:
            return False

        # Find the separator after the JSON
        separator_pos = decoded.find(b":", json_end)
        if separator_pos < 0:
            return False

        # Parse parameters from JSON
        param_bytes = decoded[: json_end + 1]
        params = json.loads(param_bytes)

        # Extract salt and hash
        salt = decoded[separator_pos + 1 : separator_pos + 17]  # 16 bytes for salt
        stored_hash = decoded[separator_pos + 17 :]  # Remaining bytes for hash

        # Hash the password being tested with the same parameters
        hash_to_check = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=params["n"],
            r=params["r"],
            p=params["p"],
            dklen=params["dklen"],
        )

        return hash_to_check == stored_hash
    except Exception:
        return False
