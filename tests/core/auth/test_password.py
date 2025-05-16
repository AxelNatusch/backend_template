import base64
import json
import hashlib
import time

from src.core.auth.password import get_password_hash, verify_password


def test_get_password_hash_returns_valid_string():
    """Test that get_password_hash returns a non-empty string."""
    password = "SecurePassword123"
    
    hash_result = get_password_hash(password)
    
    assert isinstance(hash_result, str)
    assert len(hash_result) > 0


def test_get_password_hash_format():
    """Test to examine the format of the password hash."""
    password = "TestPassword123"
    # Use very small parameters for quick testing
    n_value = 2**5
    r_value = 4
    p_value = 1
    dklen_value = 16
    
    # Generate hash
    hash_result = get_password_hash(
        password, 
        n=n_value, 
        r=r_value, 
        p=p_value, 
        dklen=dklen_value
    )
    
    # Manually decode and parse the hash
    decoded = base64.b64decode(hash_result)
    
    # Find the position where the JSON parameters end
    json_end = -1
    brace_count = 0
    for i, c in enumerate(decoded):
        if c == ord('{'):
            brace_count += 1
        elif c == ord('}'):
            brace_count -= 1
            if brace_count == 0:
                json_end = i
                break
    
    assert json_end > 0, "Could not find end of JSON object"
    
    # Extract JSON parameters
    json_bytes = decoded[:json_end + 1]
    params = json.loads(json_bytes)
    
    # Verify parameters match what we expect
    assert params['n'] == n_value
    assert params['r'] == r_value
    assert params['p'] == p_value
    assert params['dklen'] == dklen_value
    
    # Find the separator after the JSON
    separator_pos = decoded.find(b':', json_end)
    assert separator_pos > 0, "Separator not found after JSON"
    
    # Extract salt and hash
    salt = decoded[separator_pos + 1:separator_pos + 17]  # 16 bytes for salt
    stored_hash = decoded[separator_pos + 17:]  # Remaining bytes for hash
    
    # Create hash manually for verification
    expected_hash = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=n_value,
        r=r_value,
        p=p_value,
        dklen=dklen_value
    )
    
    # Verify hash matches
    assert stored_hash == expected_hash


def test_get_password_hash_uses_provided_parameters():
    """Test that get_password_hash uses custom parameters when provided."""
    password = "SecurePassword123"
    custom_n = 2**5  # Using lower values for testing
    custom_r = 4
    custom_p = 2
    custom_dklen = 16
    
    hash_result = get_password_hash(password, n=custom_n, r=custom_r, p=custom_p, dklen=custom_dklen)
    
    # Decode the base64
    decoded = base64.b64decode(hash_result)
    
    # Parse the JSON part by finding matching braces
    json_end = -1
    brace_count = 0
    for i, c in enumerate(decoded):
        if c == ord('{'):
            brace_count += 1
        elif c == ord('}'):
            brace_count -= 1
            if brace_count == 0:
                json_end = i
                break
    
    assert json_end > 0, "Could not find end of JSON object"
    
    # Extract and parse JSON
    json_bytes = decoded[:json_end + 1]
    params = json.loads(json_bytes)
    
    # Verify the parameters
    assert params['n'] == custom_n
    assert params['r'] == custom_r
    assert params['p'] == custom_p
    assert params['dklen'] == custom_dklen


def test_different_passwords_produce_different_hashes():
    """Test that different passwords produce different hash values."""
    password1 = "Password123"
    password2 = "Password124"
    
    hash1 = get_password_hash(password1)
    hash2 = get_password_hash(password2)
    
    assert hash1 != hash2


def test_same_password_with_different_salt_produces_different_hash():
    """Test that the same password produces different hashes due to random salt."""
    password = "SamePassword"
    
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    assert hash1 != hash2


def test_verify_password_with_correct_password():
    """Test that verify_password returns True for correct password."""
    password = "CorrectPassword123"
    
    # Use reduced parameters for faster tests
    hash_result = get_password_hash(
        password,
        n=2**3,  # Very small n for testing
        r=2,
        p=1,
        dklen=16
    )
    
    # Test verify_password function
    result = verify_password(password, hash_result)
    assert result is True


def test_verify_password_with_incorrect_password():
    """Test that verify_password returns False for incorrect password."""
    password = "CorrectPassword123"
    wrong_password = "WrongPassword123"
    
    # Use reduced parameters for faster tests
    hash_result = get_password_hash(
        password,
        n=2**3,  # Very small n for testing
        r=2,
        p=1,
        dklen=16
    )
    
    result = verify_password(wrong_password, hash_result)
    assert result is False


def test_verify_password_with_invalid_hash_format():
    """Test that verify_password returns False for invalid hash format."""
    password = "AnyPassword"
    invalid_hash = "InvalidHashFormat"
    
    result = verify_password(password, invalid_hash)
    assert result is False


def test_verify_password_with_malformed_json():
    """Test that verify_password handles malformed JSON in hash."""
    password = "AnyPassword"
    # Create a malformed hash with invalid JSON
    malformed_data = b'{"invalid json":' + b':' + b'x' * 20
    malformed_hash = base64.b64encode(malformed_data).decode('utf-8')
    
    result = verify_password(password, malformed_hash)
    assert result is False


# Edge Cases and Security Tests

def test_empty_password():
    """Test that empty password can be hashed and verified."""
    password = ""
    
    # Generate hash with minimal parameters for speed
    hash_result = get_password_hash(
        password,
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Verify the empty password works
    result = verify_password(password, hash_result)
    assert result is True
    
    # Verify a non-empty password fails
    result = verify_password("not_empty", hash_result)
    assert result is False


def test_long_password():
    """Test that very long passwords can be hashed and verified."""
    # Create a long password (10KB)
    password = "x" * 10240
    
    # Generate hash with minimal parameters for speed
    hash_result = get_password_hash(
        password,
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Verify the long password
    result = verify_password(password, hash_result)
    assert result is True


def test_special_characters_password():
    """Test passwords with special characters."""
    # Password with a mix of special characters
    password = "P@$$w0rd!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    
    # Generate hash
    hash_result = get_password_hash(
        password,
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Verify the password with special characters
    result = verify_password(password, hash_result)
    assert result is True


def test_unicode_password():
    """Test passwords with unicode characters."""
    # Password with unicode characters
    password = "ùñîçôdé_Pässwörd_🔒👍"
    
    # Generate hash
    hash_result = get_password_hash(
        password,
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Verify the unicode password
    result = verify_password(password, hash_result)
    assert result is True


def test_salt_length():
    """Test that salt is always 16 bytes long."""
    for _ in range(5):  # Test multiple hashes
        hash_result = get_password_hash("test_password", n=2**3, r=2, p=1, dklen=16)
        
        # Decode the hash
        decoded = base64.b64decode(hash_result)
        
        # Find JSON end
        json_end = -1
        brace_count = 0
        for i, c in enumerate(decoded):
            if c == ord('{'):
                brace_count += 1
            elif c == ord('}'):
                brace_count -= 1
                if brace_count == 0:
                    json_end = i
                    break
        
        # Find separator and extract salt
        separator_pos = decoded.find(b':', json_end)
        salt = decoded[separator_pos + 1:separator_pos + 17]
        
        # Verify salt length
        assert len(salt) == 16, "Salt should be exactly 16 bytes"


def test_extreme_parameter_values():
    """Test with extreme (but valid) parameter values."""
    # Very small parameters
    small_hash = get_password_hash(
        "test_password",
        n=2**1,  # Smallest valid n (power of 2)
        r=1,      # Smallest valid r
        p=1,      # Smallest valid p
        dklen=1   # Smallest useful dklen
    )
    
    # Verify small parameters
    assert verify_password("test_password", small_hash) is True
    
    # Larger parameters (but not too large to make test run forever)
    large_hash = get_password_hash(
        "test_password",
        n=2**8,    # Larger n but still reasonable for test
        r=16,      # Larger r
        p=2,       # Larger p
        dklen=64   # Larger dklen
    )
    
    # Verify larger parameters
    assert verify_password("test_password", large_hash) is True


def test_timing_consistency():
    """Test that verification takes similar time for correct and incorrect passwords.
    
    This is a basic check for timing attacks. A more comprehensive test would require
    statistical analysis of multiple runs.
    """
    password = "TestPassword123"
    wrong_password = "WrongPassword123"
    
    # Generate hash with minimal parameters for speed in tests
    hash_result = get_password_hash(
        password,
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Measure time for correct password
    start_time = time.time()
    verify_password(password, hash_result)
    correct_time = time.time() - start_time
    
    # Measure time for incorrect password
    start_time = time.time()
    verify_password(wrong_password, hash_result)
    incorrect_time = time.time() - start_time
    
    # The times shouldn't be drastically different
    # This is a very rough check and might be flaky on some systems
    # But it can catch obvious timing differences
    assert abs(correct_time - incorrect_time) < 0.1, "Significant timing difference detected"


def test_parameter_types():
    """Test that parameters are correctly stored as integers."""
    hash_result = get_password_hash(
        "test_password",
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Decode and parse JSON
    decoded = base64.b64decode(hash_result)
    json_end = -1
    brace_count = 0
    for i, c in enumerate(decoded):
        if c == ord('{'):
            brace_count += 1
        elif c == ord('}'):
            brace_count -= 1
            if brace_count == 0:
                json_end = i
                break
    
    json_bytes = decoded[:json_end + 1]
    params = json.loads(json_bytes)
    
    # Verify parameter types
    assert isinstance(params['n'], int)
    assert isinstance(params['r'], int)
    assert isinstance(params['p'], int)
    assert isinstance(params['dklen'], int)


def test_non_power_of_two_n():
    """Test that n parameter must be a power of 2.
    
    The scrypt algorithm requires n to be a power of 2. If a non-power of 2 is 
    provided, it would likely cause issues or be rejected by the underlying library.
    This test verifies the behavior with non-power-of-2 values.
    """
    password = "test_password"
    non_power_of_two = 100  # Not a power of 2
    
    try:
        # Try to hash with non-power-of-2 n
        hash_result = get_password_hash(
            password,
            n=non_power_of_two,
            r=2,
            p=1,
            dklen=16
        )
        
        # If we got here without an exception, let's verify the hash works
        # The function might have corrected the value or handled it differently
        decoded = base64.b64decode(hash_result)
        
        # Find and parse JSON to see what actual n value was used
        json_end = -1
        brace_count = 0
        for i, c in enumerate(decoded):
            if c == ord('{'):
                brace_count += 1
            elif c == ord('}'):
                brace_count -= 1
                if brace_count == 0:
                    json_end = i
                    break
        
        json_bytes = decoded[:json_end + 1]
        params = json.loads(json_bytes)
        
        # Check if n is a power of 2 (n & (n-1) == 0 for powers of 2)
        assert (params['n'] & (params['n'] - 1)) == 0, "n parameter should be a power of 2"
        
        # Try to verify with this hash
        assert verify_password(password, hash_result) is True
        
    except ValueError as e:
        # It's also acceptable if the function raises an error for invalid parameters
        assert "power of 2" in str(e).lower() or "invalid" in str(e).lower(), \
            "Expected error about power of 2 requirement"


def test_zero_or_negative_parameters():
    """Test that parameters can't be zero or negative."""
    password = "test_password"
    
    # Test with zero and negative values for each parameter
    for param_name, param_value in [
        ('n', 0),
        ('n', -2),
        ('r', 0),
        ('r', -1),
        ('p', 0),
        ('p', -1),
        ('dklen', 0),
        ('dklen', -16)
    ]:
        try:
            # Create parameters dict with the invalid parameter
            params = {
                'n': 2**3,
                'r': 2,
                'p': 1,
                'dklen': 16
            }
            params[param_name] = param_value
            
            # Try to hash with invalid parameter
            hash_result = get_password_hash(password, **params)
            
            # If we get here without an exception, verify the function handled it properly
            # by checking the stored parameter in the hash - it should not be the invalid value
            decoded = base64.b64decode(hash_result)
            
            # Find and parse JSON
            json_end = -1
            brace_count = 0
            for i, c in enumerate(decoded):
                if c == ord('{'):
                    brace_count += 1
                elif c == ord('}'):
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i
                        break
            
            json_bytes = decoded[:json_end + 1]
            stored_params = json.loads(json_bytes)
            
            # The parameter should not be the invalid value
            assert stored_params[param_name] != param_value, \
                f"Parameter {param_name} should not accept {param_value}"
            
            # The parameter should be positive
            assert stored_params[param_name] > 0, \
                f"Parameter {param_name} should be positive"
            
        except (ValueError, TypeError):
            # It's also acceptable if the function raises an error for invalid parameters
            # scrypt may raise different types of exceptions in different versions
            pass


def test_multiple_colons_in_json():
    """Test handling of JSON with colons in it."""
    # Create a password with colons to ensure JSON will have them
    password = "password:with:colons"
    
    # Generate hash
    hash_result = get_password_hash(
        password,
        n=2**3,
        r=2,
        p=1,
        dklen=16
    )
    
    # Verify it works
    assert verify_password(password, hash_result) is True 