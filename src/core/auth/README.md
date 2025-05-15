# Core Authentication Utilities

## Overview

The Core Authentication module provides essential security primitives and utilities that power the application's auth system. This module implements industry-standard cryptographic approaches for secure password management, JWT token handling, and API key operations.

## Components

### Password Utilities (`password.py`)

Provides secure password hashing and verification using the `scrypt` key derivation function:

- **Hashing**: Uses the strong `scrypt` algorithm with configurable parameters
- **Storage**: Stores salt, hash parameters, and the derived key together
- **Verification**: Constant-time comparison to prevent timing attacks
- **Security**: Implements modern password hashing best practices

Key functions:
- `get_password_hash(password)`: Creates a secure hash with random salt
- `verify_password(plain_password, hashed_password)`: Validates passwords against stored hashes

### JWT Token Utilities (`jwt.py`)

Implements JSON Web Token (JWT) functionality for stateless authentication:

- **Token Generation**: Creates signed tokens with customizable expiration
- **Token Verification**: Validates token signatures and expiration
- **Payload Handling**: Manages user data within token claims
- **Token Types**: Supports both access and refresh tokens

Key functions:
- `create_access_token(user_id, username, email, role)`: Generates short-lived access tokens
- `create_refresh_token(user_id)`: Creates longer-lived refresh tokens
- `verify_token(token)`: Validates token authenticity and expiration
- `decode_token(token)`: Extracts payload from tokens without verification

### API Key Utilities (`api_key_utils.py`)

Provides utilities for API key management:

- **Key Generation**: Creates cryptographically secure random keys
- **Key Hashing**: Securely stores only hashed versions of keys
- **Validation**: Verifies keys against stored hashes
- **Expiration Checking**: Manages key lifetime and validity periods

Key functions:
- `_generate_api_key()`: Creates a new secure API key with prefix
- `_hash_api_key(api_key)`: Hashes keys for secure database storage
- `_verify_api_key(api_key, stored_key_hash)`: Validates keys against stored hashes
- `_is_api_key_expired(expires_at)`: Checks if a key's expiration date has passed
- `_validate_api_key(api_key, stored_key_hash, expires_at)`: Complete validation with error handling

## Security Considerations

### Password Security
- Uses `scrypt` with tunable work factors for future-proofing
- Includes salt to prevent rainbow table attacks
- Stores parameters alongside hash for algorithm agility

### JWT Security
- Short-lived access tokens minimize risk window
- Token refresh mechanism with rotation
- Proper signature verification using secret keys

### API Key Security
- High-entropy random generation
- Keys are prefix-identifiable but still secure
- Only hashed versions stored in database
- Built-in expiration handling
- Constant-time comparison for hash verification

## Implementation Notes

These utilities are designed to be:

1. **Secure by default**: Following cryptographic best practices
2. **Low-level**: Providing primitives for higher-level authentication services
3. **Self-contained**: Minimal dependencies on other system components
4. **Well-documented**: Clear purpose and usage patterns
5. **Maintainable**: Structured for future security updates

## Dependencies

- Python's standard library cryptography modules
- PyJWT for token handling
- FastAPI for HTTP exceptions
- Application configuration settings 