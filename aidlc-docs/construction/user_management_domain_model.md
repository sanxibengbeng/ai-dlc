# User Management & Authentication Service - Domain Model

## Overview

This document defines the domain model for the User Management & Authentication Service, which handles user account creation, authentication, and basic profile management for Solution Architects and Sales Managers. The model supports the user stories US-SA-1 and US-SM-1 for account creation with email verification.

## Core Domain Components

### 1. User Component Model (From Shared Model)

The User component represents basic user information across the system and serves as the foundation for authentication.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the user | Yes |
| name | String | Full name of the user | Yes |
| email | String | Email address (used for login) | Yes |
| role | Enum | User role in the system (SolutionArchitect, SalesManager) | Yes |
| employeeId | String | Company employee ID (pure number) | Yes |
| department | String | Department or business unit | Yes |
| jobTitle | String | Official job title | Yes |
| isActive | Boolean | Whether the user account is active | Yes |
| createdAt | DateTime | When the user account was created | Yes |
| lastLoginAt | DateTime | When the user last logged in | No |
| profilePictureUrl | String | URL to profile picture | No |
| phoneNumber | String | Contact phone number | No |

#### Sample Data

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jane Smith",
  "email": "jane.smith@company.com",
  "role": "SolutionArchitect",
  "employeeId": "12345",
  "department": "Cloud Solutions",
  "jobTitle": "Senior Solution Architect",
  "isActive": true,
  "createdAt": "2025-01-15T08:30:00Z",
  "lastLoginAt": "2025-07-21T14:22:10Z",
  "profilePictureUrl": null,
  "phoneNumber": "+1-555-123-4567"
}
```

### 2. UserCredentials Component Model

The UserCredentials component manages password storage and authentication credentials for users.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the credentials | Yes |
| userId | UUID | Reference to the User entity | Yes |
| passwordHash | String | Hashed password using bcrypt | Yes |
| passwordSalt | String | Salt used for password hashing | Yes |
| passwordLastChanged | DateTime | When the password was last changed | Yes |
| failedLoginAttempts | Integer | Number of consecutive failed login attempts | Yes |
| accountLockedUntil | DateTime | Account lockout expiration time | No |
| mustChangePassword | Boolean | Whether user must change password on next login | Yes |
| createdAt | DateTime | When the credentials were created | Yes |
| updatedAt | DateTime | When the credentials were last updated | Yes |

#### Sample Data

```json
{
  "id": "660f9511-f30c-52e5-b827-557766551111",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "passwordHash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G",
  "passwordSalt": "$2b$12$LQv3c1yqBWVHxkd0LHAkCO",
  "passwordLastChanged": "2025-01-15T08:30:00Z",
  "failedLoginAttempts": 0,
  "accountLockedUntil": null,
  "mustChangePassword": false,
  "createdAt": "2025-01-15T08:30:00Z",
  "updatedAt": "2025-01-15T08:30:00Z"
}
```

### 3. EmailVerification Component Model

The EmailVerification component manages the email verification process for account activation.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the verification | Yes |
| userId | UUID | Reference to the User entity | Yes |
| email | String | Email address to be verified | Yes |
| verificationToken | String | Unique token for verification | Yes |
| tokenExpiresAt | DateTime | When the verification token expires (1 week) | Yes |
| isVerified | Boolean | Whether the email has been verified | Yes |
| verifiedAt | DateTime | When the email was verified | No |
| createdAt | DateTime | When the verification was created | Yes |
| resendCount | Integer | Number of times verification email was resent | Yes |
| lastResendAt | DateTime | When verification email was last resent | No |

#### Sample Data

```json
{
  "id": "770a0622-a41d-63f6-c938-668877662222",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "jane.smith@company.com",
  "verificationToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenExpiresAt": "2025-01-22T08:30:00Z",
  "isVerified": true,
  "verifiedAt": "2025-01-15T10:45:00Z",
  "createdAt": "2025-01-15T08:30:00Z",
  "resendCount": 0,
  "lastResendAt": null
}
```

### 4. PasswordReset Component Model

The PasswordReset component manages password reset requests and tokens.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the password reset | Yes |
| userId | UUID | Reference to the User entity | Yes |
| resetToken | String | Unique token for password reset | Yes |
| tokenExpiresAt | DateTime | When the reset token expires (24 hours) | Yes |
| isUsed | Boolean | Whether the reset token has been used | Yes |
| usedAt | DateTime | When the reset token was used | No |
| createdAt | DateTime | When the reset request was created | Yes |
| ipAddress | String | IP address from which reset was requested | No |
| userAgent | String | User agent from which reset was requested | No |

#### Sample Data

```json
{
  "id": "880b1733-b52e-74a7-da49-779988773333",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "resetToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenExpiresAt": "2025-07-24T08:30:00Z",
  "isUsed": false,
  "usedAt": null,
  "createdAt": "2025-07-23T08:30:00Z",
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### 5. AuthenticationToken Component Model

The AuthenticationToken component manages JWT tokens for stateless authentication.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the token | Yes |
| userId | UUID | Reference to the User entity | Yes |
| tokenHash | String | Hash of the JWT token for revocation | Yes |
| tokenType | Enum | Type of token (ACCESS, REFRESH) | Yes |
| expiresAt | DateTime | When the token expires | Yes |
| isRevoked | Boolean | Whether the token has been revoked | Yes |
| revokedAt | DateTime | When the token was revoked | No |
| revokedReason | String | Reason for token revocation | No |
| createdAt | DateTime | When the token was created | Yes |
| ipAddress | String | IP address from which token was created | No |
| userAgent | String | User agent from which token was created | No |

#### Sample Data

```json
{
  "id": "990c2844-c63f-85b8-eb5a-88aa99884444",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "tokenHash": "sha256:a1b2c3d4e5f6...",
  "tokenType": "ACCESS",
  "expiresAt": "2025-07-24T08:30:00Z",
  "isRevoked": false,
  "revokedAt": null,
  "revokedReason": null,
  "createdAt": "2025-07-23T08:30:00Z",
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### 6. SecurityAuditLog Component Model

The SecurityAuditLog component tracks security-related events for audit purposes.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the audit log entry | Yes |
| userId | UUID | Reference to the User entity (if applicable) | No |
| eventType | Enum | Type of security event | Yes |
| eventDescription | String | Description of the security event | Yes |
| success | Boolean | Whether the event was successful | Yes |
| ipAddress | String | IP address from which event occurred | No |
| userAgent | String | User agent from which event occurred | No |
| additionalData | JSON | Additional event-specific data | No |
| createdAt | DateTime | When the event occurred | Yes |

#### Event Types Enum
- USER_REGISTRATION
- EMAIL_VERIFICATION
- LOGIN_SUCCESS
- LOGIN_FAILURE
- PASSWORD_CHANGE
- PASSWORD_RESET_REQUEST
- PASSWORD_RESET_COMPLETE
- ACCOUNT_LOCKED
- ACCOUNT_UNLOCKED
- TOKEN_REVOKED

#### Sample Data

```json
{
  "id": "aa1d3955-d74a-96c9-fc6b-99bb00995555",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "LOGIN_SUCCESS",
  "eventDescription": "User successfully logged in",
  "success": true,
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "additionalData": {
    "loginMethod": "email_password",
    "sessionDuration": "24h"
  },
  "createdAt": "2025-07-23T08:30:00Z"
}
```

## Component Relationships

### Relationship Diagram

```
User (1) ←→ (1) UserCredentials
User (1) ←→ (0..n) EmailVerification
User (1) ←→ (0..n) PasswordReset
User (1) ←→ (0..n) AuthenticationToken
User (1) ←→ (0..n) SecurityAuditLog
```

### Relationship Descriptions

1. **User ↔ UserCredentials**: One-to-one relationship. Each user has exactly one set of credentials.

2. **User ↔ EmailVerification**: One-to-many relationship. A user can have multiple email verification records (for resends or email changes).

3. **User ↔ PasswordReset**: One-to-many relationship. A user can have multiple password reset requests over time.

4. **User ↔ AuthenticationToken**: One-to-many relationship. A user can have multiple active tokens (access and refresh tokens).

5. **User ↔ SecurityAuditLog**: One-to-many relationship. A user can have multiple security audit log entries.

## Business Logic and Behaviors

### User Registration Workflow

1. **Registration Request**: User submits registration form with required fields
2. **Validation**: System validates email format, employee ID format (pure number), and required fields
3. **Uniqueness Check**: System verifies email and employee ID are unique
4. **User Creation**: System creates User entity with isActive = false
5. **Credentials Creation**: System creates UserCredentials with hashed password
6. **Email Verification**: System creates EmailVerification record and sends verification email
7. **Audit Logging**: System logs USER_REGISTRATION event

### Email Verification Workflow

1. **Token Generation**: System generates unique verification token with 1-week expiration
2. **Email Sending**: System sends verification email with activation link
3. **Token Validation**: User clicks link, system validates token and expiration
4. **Account Activation**: System sets User.isActive = true and EmailVerification.isVerified = true
5. **Audit Logging**: System logs EMAIL_VERIFICATION event

### Authentication Workflow

1. **Login Request**: User submits email and password
2. **User Lookup**: System finds user by email
3. **Account Status Check**: System verifies user is active and not locked
4. **Password Verification**: System verifies password against stored hash
5. **Token Generation**: System generates JWT access token
6. **Token Storage**: System creates AuthenticationToken record
7. **Audit Logging**: System logs LOGIN_SUCCESS or LOGIN_FAILURE event

### Password Reset Workflow

1. **Reset Request**: User requests password reset with email
2. **User Lookup**: System finds user by email
3. **Token Generation**: System creates PasswordReset record with 24-hour expiration
4. **Email Sending**: System sends password reset email
5. **Token Validation**: User clicks link, system validates token
6. **Password Update**: User sets new password, system updates UserCredentials
7. **Token Invalidation**: System marks PasswordReset as used
8. **Audit Logging**: System logs PASSWORD_RESET_REQUEST and PASSWORD_RESET_COMPLETE events

## Data Validation Rules

### Email Validation
- Must be valid email format (RFC 5322 compliant)
- Must be unique across all users
- Case-insensitive comparison

### Password Validation
- Minimum 6 characters
- No maximum length restriction
- All character types allowed

### Employee ID Validation
- Must be pure numeric string
- Must be unique across all users
- No leading zeros required

### User Role Validation
- Must be one of: SolutionArchitect, SalesManager
- Cannot be changed after account creation

## Security Policies

### Password Security
- Passwords hashed using bcrypt with salt rounds = 12
- Password history not maintained (as per requirements)
- No password complexity requirements beyond minimum length

### Account Lockout Policy
- Account locked after 5 consecutive failed login attempts
- Lockout duration: 30 minutes
- Lockout counter resets after successful login

### Token Security
- JWT tokens signed with HS256 algorithm
- Access token expiration: 24 hours
- No refresh token implementation (stateless approach)
- Tokens can be revoked by storing hash in AuthenticationToken table

### Email Verification Security
- Verification tokens expire after 1 week
- Maximum 3 resend attempts per verification request
- Tokens are single-use only

## Integration Points

### Email Service Integration
- **Purpose**: Send verification and password reset emails
- **Interface**: Email service API with template support
- **Error Handling**: Graceful degradation if email service unavailable
- **Retry Logic**: Exponential backoff for failed email sends

### Audit Service Integration
- **Purpose**: Centralized security event logging
- **Interface**: Asynchronous event publishing
- **Data**: All security events logged to SecurityAuditLog table
- **Retention**: Audit logs retained according to company policy

## API Contract Implications

### Registration Endpoint
```
POST /api/auth/register
Request: { name, email, employeeId, department, jobTitle, password, role }
Response: { userId, message: "Verification email sent" }
```

### Email Verification Endpoint
```
GET /api/auth/verify-email?token={verificationToken}
Response: { success: true, message: "Account activated" }
```

### Login Endpoint
```
POST /api/auth/login
Request: { email, password }
Response: { accessToken, user: { id, name, email, role } }
```

### Password Reset Request Endpoint
```
POST /api/auth/password-reset-request
Request: { email }
Response: { message: "Password reset email sent" }
```

### Password Reset Completion Endpoint
```
POST /api/auth/password-reset-complete
Request: { resetToken, newPassword }
Response: { success: true, message: "Password updated" }
```

## Error Handling

### Registration Errors
- Email already exists: HTTP 409 Conflict
- Employee ID already exists: HTTP 409 Conflict
- Invalid email format: HTTP 400 Bad Request
- Invalid employee ID format: HTTP 400 Bad Request
- Missing required fields: HTTP 400 Bad Request

### Authentication Errors
- Invalid credentials: HTTP 401 Unauthorized
- Account not activated: HTTP 403 Forbidden
- Account locked: HTTP 423 Locked
- Account inactive: HTTP 403 Forbidden

### Token Errors
- Invalid token: HTTP 401 Unauthorized
- Expired token: HTTP 401 Unauthorized
- Revoked token: HTTP 401 Unauthorized

## Implementation Notes

### Database Considerations
- Use UUID primary keys for all entities
- Index on User.email and User.employeeId for uniqueness constraints
- Index on EmailVerification.verificationToken and PasswordReset.resetToken
- Soft delete implementation: Use User.isActive flag instead of hard delete

### Performance Considerations
- Password hashing is CPU-intensive; consider async processing
- Email sending should be asynchronous to avoid blocking requests
- Token validation should be fast; consider caching user data

### Security Considerations
- All sensitive data (passwords, tokens) must be hashed/encrypted
- Implement rate limiting on authentication endpoints
- Log all security events for monitoring and compliance
- Use HTTPS for all authentication-related endpoints

## Use Case Scenarios

### Scenario 1: Solution Architect Registration
1. **Actor**: New Solution Architect employee
2. **Precondition**: User has company email and employee ID
3. **Flow**:
   - User navigates to registration page
   - User fills form: name="John Doe", email="john.doe@company.com", employeeId="67890", department="Cloud Solutions", jobTitle="Solution Architect", password="mypass123", role="SolutionArchitect"
   - System validates all fields and creates User (isActive=false) and UserCredentials
   - System creates EmailVerification record and sends verification email
   - User receives email and clicks verification link
   - System activates account (isActive=true) and marks email as verified
   - User can now log in successfully
4. **Postcondition**: Active user account ready for use

### Scenario 2: Sales Manager Registration
1. **Actor**: New Sales Manager employee
2. **Precondition**: User has company email and employee ID
3. **Flow**:
   - User navigates to registration page
   - User fills form: name="Sarah Wilson", email="sarah.wilson@company.com", employeeId="54321", department="Sales", jobTitle="Senior Sales Manager", password="secure456", role="SalesManager"
   - System validates all fields and creates User (isActive=false) and UserCredentials
   - System creates EmailVerification record and sends verification email
   - User receives email and clicks verification link
   - System activates account (isActive=true) and marks email as verified
   - User can now log in successfully
4. **Postcondition**: Active user account ready for use

### Scenario 3: User Authentication
1. **Actor**: Registered and activated user
2. **Precondition**: User has active account
3. **Flow**:
   - User submits login credentials
   - System validates email and password
   - System generates JWT access token
   - System creates AuthenticationToken record
   - System logs successful login event
   - User receives access token for API calls
4. **Postcondition**: User is authenticated and can access protected resources

### Scenario 4: Password Reset
1. **Actor**: User who forgot password
2. **Precondition**: User has registered account
3. **Flow**:
   - User requests password reset with email
   - System creates PasswordReset record and sends reset email
   - User clicks reset link and provides new password
   - System validates token and updates UserCredentials
   - System marks reset token as used
   - User can log in with new password
4. **Postcondition**: User has new password and can authenticate

## Component Relationship Diagram

```
┌─────────────────┐    1:1    ┌─────────────────┐
│      User       │◄─────────►│ UserCredentials │
│                 │           │                 │
│ - id            │           │ - passwordHash  │
│ - name          │           │ - passwordSalt  │
│ - email         │           │ - failedAttempts│
│ - role          │           └─────────────────┘
│ - employeeId    │
│ - isActive      │    1:n    ┌─────────────────┐
└─────────────────┘◄─────────►│EmailVerification│
         │                    │                 │
         │                    │ - verificationToken
         │                    │ - tokenExpiresAt│
         │                    │ - isVerified    │
         │                    └─────────────────┘
         │
         │         1:n    ┌─────────────────┐
         └───────────────►│ PasswordReset   │
         │                │                 │
         │                │ - resetToken    │
         │                │ - tokenExpiresAt│
         │                │ - isUsed        │
         │                └─────────────────┘
         │
         │         1:n    ┌─────────────────┐
         └───────────────►│AuthenticationToken
         │                │                 │
         │                │ - tokenHash     │
         │                │ - tokenType     │
         │                │ - expiresAt     │
         │                └─────────────────┘
         │
         │         1:n    ┌─────────────────┐
         └───────────────►│SecurityAuditLog │
                          │                 │
                          │ - eventType     │
                          │ - eventDescription
                          │ - success       │
                          └─────────────────┘
```

## Validation Summary

### User Story US-SA-1 Compliance
✅ **Registration Page Access**: API endpoint `/api/auth/register` provides registration capability
✅ **Required Fields**: All fields (name, email, employeeId, department, jobTitle) included in User component
✅ **Email Format Validation**: RFC 5322 compliant validation implemented
✅ **Email Uniqueness**: Database constraint and validation logic ensure uniqueness
✅ **Verification Email**: EmailVerification component handles token generation and email sending
✅ **Registration Confirmation**: Registration workflow provides confirmation response
✅ **Login After Activation**: Authentication workflow allows login only for active accounts

### User Story US-SM-1 Compliance
✅ **Registration Page Access**: Same API endpoint supports Sales Manager registration
✅ **Required Fields**: Same field validation applies to Sales Manager role
✅ **Email Format Validation**: Same validation rules apply
✅ **Email Uniqueness**: Same uniqueness constraints apply
✅ **Verification Email**: Same EmailVerification process applies
✅ **Registration Confirmation**: Same confirmation workflow applies
✅ **Login After Activation**: Same authentication rules apply

### Key Capabilities Compliance
✅ **Account Registration**: Comprehensive registration workflow with email verification
✅ **Authentication**: JWT-based stateless authentication with token management
✅ **Profile Management**: User component supports profile information updates
✅ **Role Management**: Role enum supports SolutionArchitect and SalesManager roles
✅ **Account Lifecycle**: isActive flag supports activation/deactivation with soft delete

This domain model provides a complete foundation for implementing the User Management & Authentication Service according to all specified requirements and user stories.