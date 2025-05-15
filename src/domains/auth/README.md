# Authentication Domain

## Overview

The Authentication Domain provides a comprehensive user authentication and authorization system. It includes user management, secure login/logout functionality, JWT token handling, and API key generation/validation for programmatic access.

## Components

### Models

- **User**: Core user model with properties like username, email, password (hashed), role, and activity status.
- **UserRole**: Enum defining different user roles (USER, ADMIN).
- **API Keys**: Long-lived authentication tokens for programmatic API access.
- **Tokens**: JWT tokens for web session authentication (access/refresh).

### Services

#### Auth Service
- **User Registration**: Creates new user accounts with proper validation.
- **Login**: Authenticates users and issues JWT tokens.
- **Token Refresh**: Implements token rotation for security.

#### User Service
- **User CRUD**: Manages user creation, retrieval, updating, and deletion.
- **User Validation**: Ensures username/email uniqueness.

#### API Key Service
- **Key Generation**: Creates secure, unique API keys for users.
- **Key Validation**: Verifies API keys during requests.
- **Key Management**: Allows listing, revoking, and deleting API keys.

### Repositories

Handles direct database interactions for:
- **UserRepository**: User data persistence.
- **APIKeyRepository**: API key storage and retrieval.

### API Endpoints

#### Auth Endpoints (`/auth`)
- POST `/register`: Create new user (admin only)
- POST `/login`: Authenticate and receive access/refresh tokens
- POST `/refresh`: Get new tokens using refresh token
- GET `/me`: Get current user profile
- GET `/me-api-key`: Get user profile via API key

#### API Key Endpoints (`/auth/api_keys`)
- POST `/`: Create new API key
- GET `/`: List all user's API keys
- PUT `/revoke`: Revoke an API key by value
- PUT `/revoke/{id}`: Revoke an API key by ID
- DELETE `/{id}`: Permanently delete an API key

## Security Architecture

### Password Security
- Passwords are never stored in plain text
- Secure hashing using industry standard algorithms

### Token Security
- Short-lived access tokens (JWT)
- Refresh token rotation
- Token payload includes user identity and permissions

### API Key Security
- Only hash of key stored in database
- Original key shown only once at creation
- Keys can be time-limited with automatic expiration
- Usage tracking for audit purposes

## Usage Examples

### User Authentication Flow

1. Register user (admin only) with username, email, and password
2. User logs in with credentials
3. System returns access token (short-lived) and refresh token
4. Client includes access token in Authorization header
5. When access token expires, use refresh token to get new tokens

### API Key Flow

1. Authenticated user creates API key with optional expiration
2. System returns the API key (shown only once)
3. Client saves and uses API key in requests (header)
4. Server validates API key on each request
5. User can revoke or delete keys as needed

## Dependencies

- Core authentication utilities (JWT, password hashing)
- Database session management