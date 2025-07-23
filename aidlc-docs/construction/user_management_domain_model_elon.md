# User Management Domain Model

## Overview
This document defines the Domain Model for the User Management & Authentication Service, implementing user stories US-SA-1 (Solution Architect Account Creation) and US-SM-1 (Sales Manager Account Creation).

## Core Domain Entities

### 1. User Component Model

The User component represents basic user information across the system.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the user | Yes |
| name | String | Full name of the user | Yes |
| email | String | Email address (used for login) | Yes |
| role | Enum | User role in the system (SA, SalesManager, Admin) | Yes |
| employeeId | String | Company employee ID | Yes |
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
  "employeeId": "EMP12345",
  "department": "Cloud Solutions",
  "jobTitle": "Senior Solution Architect",
  "isActive": true,
  "createdAt": "2025-01-15T08:30:00Z",
  "lastLoginAt": "2025-07-21T14:22:10Z",
  "profilePictureUrl": "https://company.com/profiles/jsmith.jpg",
  "phoneNumber": "+1-555-123-4567"
}
```

### 2. UserAccount Entity

The UserAccount entity manages the account lifecycle and authentication state.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the user account | Yes |
| userId | UUID | Reference to the User entity | Yes |
| accountStatus | Enum | Status of the account (PendingVerification, Active, Inactive, Suspended) | Yes |
| emailVerified | Boolean | Whether the email has been verified | Yes |
| passwordHash | String | Hashed password for authentication | Yes |
| passwordSalt | String | Salt used for password hashing | Yes |
| failedLoginAttempts | Integer | Number of consecutive failed login attempts | Yes |
| lastFailedLoginAt | DateTime | When the last failed login attempt occurred | No |
| accountLockedUntil | DateTime | When the account lock expires (if locked) | No |
| createdAt | DateTime | When the account was created | Yes |
| updatedAt | DateTime | When the account was last updated | Yes |

#### Business Rules
- Account must be in Active status and emailVerified must be true for successful login
- Account gets locked after 5 consecutive failed login attempts for 30 minutes
- Password must meet complexity requirements (handled by domain service)

### 3. EmailVerification Entity

The EmailVerification entity manages the email verification process.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the verification | Yes |
| userId | UUID | Reference to the User entity | Yes |
| email | String | Email address being verified | Yes |
| verificationToken | String | Unique token for verification | Yes |
| tokenExpiresAt | DateTime | When the verification token expires | Yes |
| isUsed | Boolean | Whether the token has been used | Yes |
| verifiedAt | DateTime | When the email was verified | No |
| createdAt | DateTime | When the verification was created | Yes |

#### Business Rules
- Verification token expires after 24 hours
- Token can only be used once
- New verification token invalidates previous unused tokens for the same email

### 4. AuthenticationSession Entity

The AuthenticationSession entity manages user login sessions.

#### Attributes

| Attribute | Data Type | Description | Required |
|-----------|-----------|-------------|----------|
| id | UUID | Unique identifier for the session | Yes |
| userId | UUID | Reference to the User entity | Yes |
| sessionToken | String | Unique session token | Yes |
| createdAt | DateTime | When the session was created | Yes |
| expiresAt | DateTime | When the session expires | Yes |
| lastAccessedAt | DateTime | When the session was last accessed | Yes |
| ipAddress | String | IP address of the client | No |
| userAgent | String | User agent string of the client | No |
| isActive | Boolean | Whether the session is active | Yes |

#### Business Rules
- Session expires after 8 hours of inactivity
- User can have multiple active sessions
- Session token must be cryptographically secure

## Entity Relationships

1. **User** (1) ←→ (1) **UserAccount**: Each user has exactly one account
2. **User** (1) ←→ (0..*) **EmailVerification**: User can have multiple verification attempts
3. **User** (1) ←→ (0..*) **AuthenticationSession**: User can have multiple active sessions
4. **UserAccount** and **EmailVerification** are linked through the User entity
5. **AuthenticationSession** references User for session management

## Domain Services

### 1. UserRegistrationService

Handles the complete user registration workflow.

#### Responsibilities
- Validate registration data
- Check email uniqueness
- Create User and UserAccount entities
- Generate email verification token
- Trigger email verification process

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| registerUser | RegistrationRequest | RegistrationResult | Registers a new user account |
| validateRegistrationData | RegistrationRequest | ValidationResult | Validates registration input |
| checkEmailUniqueness | Email | Boolean | Checks if email is already registered |

#### Business Rules
- Email must be unique across all users
- All required fields must be provided
- Employee ID must be unique
- User role must be valid (SolutionArchitect or SalesManager)

### 2. EmailVerificationService

Manages the email verification process.

#### Responsibilities
- Generate verification tokens
- Send verification emails
- Verify email addresses
- Handle token expiration

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| sendVerificationEmail | UserId, Email | VerificationResult | Sends verification email with token |
| verifyEmail | VerificationToken | VerificationResult | Verifies email using token |
| generateVerificationToken | UserId, Email | VerificationToken | Generates secure verification token |
| isTokenValid | VerificationToken | Boolean | Checks if token is valid and not expired |

#### Business Rules
- Verification token expires after 24 hours
- Only one active verification token per user email
- Token can only be used once
- Account activation requires successful email verification

### 3. AuthenticationService

Handles user authentication and session management.

#### Responsibilities
- Authenticate user credentials
- Create and manage sessions
- Handle login/logout operations
- Manage account lockout

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| authenticateUser | Email, Password | AuthenticationResult | Authenticates user credentials |
| createSession | UserId, ClientInfo | SessionResult | Creates new authentication session |
| validateSession | SessionToken | SessionValidationResult | Validates existing session |
| terminateSession | SessionToken | Boolean | Terminates user session |
| handleFailedLogin | Email | FailedLoginResult | Handles failed login attempt |

#### Business Rules
- Account must be active and email verified for login
- Account locks after 5 consecutive failed attempts for 30 minutes
- Sessions expire after 8 hours of inactivity
- Password must match stored hash

### 4. UserProfileService

Manages user profile information updates.

#### Responsibilities
- Update user profile information
- Validate profile changes
- Handle profile picture uploads
- Manage contact information

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| updateProfile | UserId, ProfileUpdateRequest | UpdateResult | Updates user profile information |
| updateContactInfo | UserId, ContactInfo | UpdateResult | Updates contact information |
| uploadProfilePicture | UserId, ImageFile | UploadResult | Uploads and sets profile picture |
| validateProfileData | ProfileUpdateRequest | ValidationResult | Validates profile update data |

#### Business Rules
- Only the user themselves can update their profile
- Email changes require re-verification
- Profile picture must meet size and format requirements

## Domain Events

Domain events represent significant business occurrences that other parts of the system may need to react to.

### 1. UserRegistered Event

Triggered when a new user successfully registers.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the registered user |
| email | String | Email address of the user |
| role | Enum | Role of the registered user |
| registeredAt | DateTime | When the registration occurred |
| requiresEmailVerification | Boolean | Whether email verification is needed |

#### Triggered By
- UserRegistrationService.registerUser()

#### Potential Consumers
- Email service (to send welcome email)
- Audit service (to log registration)
- Analytics service (to track user growth)

### 2. EmailVerificationRequested Event

Triggered when an email verification is requested.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the user |
| email | String | Email address to verify |
| verificationToken | String | Verification token |
| expiresAt | DateTime | When the token expires |
| requestedAt | DateTime | When verification was requested |

#### Triggered By
- EmailVerificationService.sendVerificationEmail()

#### Potential Consumers
- Email service (to send verification email)
- Notification service (to track pending verifications)

### 3. EmailVerified Event

Triggered when an email address is successfully verified.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the user |
| email | String | Verified email address |
| verifiedAt | DateTime | When the email was verified |
| accountActivated | Boolean | Whether this verification activated the account |

#### Triggered By
- EmailVerificationService.verifyEmail()

#### Potential Consumers
- User account service (to activate account)
- Email service (to send confirmation)
- Analytics service (to track verification rates)

### 4. UserLoggedIn Event

Triggered when a user successfully logs in.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the logged-in user |
| sessionId | UUID | ID of the created session |
| loginAt | DateTime | When the login occurred |
| ipAddress | String | IP address of the client |
| userAgent | String | User agent of the client |

#### Triggered By
- AuthenticationService.authenticateUser()

#### Potential Consumers
- Security service (to monitor login patterns)
- Analytics service (to track user activity)
- Audit service (to log access)

### 5. UserLoggedOut Event

Triggered when a user logs out or session expires.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the user |
| sessionId | UUID | ID of the terminated session |
| logoutAt | DateTime | When the logout occurred |
| reason | Enum | Reason for logout (UserInitiated, SessionExpired, AdminTerminated) |

#### Triggered By
- AuthenticationService.terminateSession()
- Session expiration process

#### Potential Consumers
- Analytics service (to track session duration)
- Security service (to monitor logout patterns)

### 6. UserProfileUpdated Event

Triggered when a user's profile information is updated.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the user |
| updatedFields | Array of String | Names of fields that were updated |
| updatedAt | DateTime | When the update occurred |
| updatedBy | UUID | ID of the user who made the update |

#### Triggered By
- UserProfileService.updateProfile()
- UserProfileService.updateContactInfo()

#### Potential Consumers
- Audit service (to track profile changes)
- Search service (to update user indexes)
- Cache service (to invalidate cached profile data)

### 7. AccountLocked Event

Triggered when a user account is locked due to failed login attempts.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| eventId | UUID | Unique identifier for the event |
| userId | UUID | ID of the user |
| email | String | Email address of the locked account |
| lockedAt | DateTime | When the account was locked |
| lockedUntil | DateTime | When the lock expires |
| failedAttempts | Integer | Number of failed attempts that caused the lock |

#### Triggered By
- AuthenticationService.handleFailedLogin()

#### Potential Consumers
- Security service (to monitor security threats)
- Email service (to send account locked notification)
- Admin service (to alert administrators)

## Value Objects

Value objects represent concepts that are defined by their attributes rather than their identity. They are immutable and provide validation and business logic.

### 1. Email Value Object

Represents and validates email addresses.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| value | String | The email address string |

#### Validation Rules
- Must not be null or empty
- Must match valid email format (RFC 5322 compliant)
- Must not exceed 254 characters
- Domain part must be valid
- Local part must not exceed 64 characters

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| isValid() | Boolean | Validates the email format |
| getDomain() | String | Returns the domain part of the email |
| getLocalPart() | String | Returns the local part of the email |
| toString() | String | Returns the email as string |

#### Sample Usage
```
Email email = new Email("jane.smith@company.com");
if (email.isValid()) {
    String domain = email.getDomain(); // "company.com"
}
```

### 2. EmployeeId Value Object

Represents and validates employee identifiers.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| value | String | The employee ID string |

#### Validation Rules
- Must not be null or empty
- Must be alphanumeric
- Must be between 3 and 20 characters
- Must start with a letter or "EMP"
- Must be unique across the system

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| isValid() | Boolean | Validates the employee ID format |
| toString() | String | Returns the employee ID as string |

### 3. UserRole Value Object

Represents user roles in the system.

#### Enum Values
- **SolutionArchitect**: Solution Architect role
- **SalesManager**: Sales Manager role  
- **Administrator**: System Administrator role

#### Validation Rules
- Must be one of the defined enum values
- Cannot be null

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| canCreateOpportunities() | Boolean | Whether this role can create opportunities |
| canManageProfiles() | Boolean | Whether this role can manage SA profiles |
| isAdministrator() | Boolean | Whether this is an administrator role |

### 4. AccountStatus Value Object

Represents the status of a user account.

#### Enum Values
- **PendingVerification**: Account created but email not verified
- **Active**: Account is active and can be used
- **Inactive**: Account is temporarily inactive
- **Suspended**: Account is suspended due to policy violation
- **Locked**: Account is locked due to security concerns

#### Validation Rules
- Must be one of the defined enum values
- Cannot be null

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| canLogin() | Boolean | Whether login is allowed for this status |
| requiresVerification() | Boolean | Whether email verification is required |
| isActive() | Boolean | Whether the account is in active state |

### 5. Password Value Object

Represents and validates passwords (stores hash, not plain text).

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| hash | String | The hashed password |
| salt | String | The salt used for hashing |
| algorithm | String | The hashing algorithm used |

#### Validation Rules (for plain text password before hashing)
- Must be at least 8 characters long
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one digit
- Must contain at least one special character
- Must not contain common dictionary words
- Must not be the same as the last 5 passwords

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| verify() | plainTextPassword | Boolean | Verifies password against hash |
| isExpired() | maxAgeDays | Boolean | Checks if password is expired |
| meetsComplexity() | plainTextPassword | Boolean | Validates password complexity |

### 6. VerificationToken Value Object

Represents email verification tokens.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| value | String | The token string |
| expiresAt | DateTime | When the token expires |

#### Validation Rules
- Must be cryptographically secure (minimum 32 characters)
- Must be URL-safe
- Must have expiration time
- Must be unique

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| isExpired() | Boolean | Checks if token is expired |
| isValid() | Boolean | Validates token format and expiration |
| toString() | String | Returns the token as string |

### 7. SessionToken Value Object

Represents authentication session tokens.

#### Attributes

| Attribute | Data Type | Description |
|-----------|-----------|-------------|
| value | String | The session token string |
| expiresAt | DateTime | When the session expires |

#### Validation Rules
- Must be cryptographically secure (minimum 32 characters)
- Must be URL-safe
- Must have expiration time
- Must be unique

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| isExpired() | Boolean | Checks if session is expired |
| isValid() | Boolean | Validates token format and expiration |
| toString() | String | Returns the token as string |

## Aggregates and Aggregate Roots

Aggregates define consistency boundaries and encapsulate business logic. Each aggregate has one aggregate root that controls access to the aggregate.

### 1. User Aggregate

The User aggregate is the primary aggregate root that manages user identity, account status, and authentication.

#### Aggregate Root: User Entity

The User entity serves as the aggregate root and controls all operations within the user aggregate boundary.

#### Aggregate Members
- **User** (Aggregate Root)
- **UserAccount** (Entity)
- **EmailVerification** (Entity Collection)
- **AuthenticationSession** (Entity Collection)

#### Aggregate Boundaries
The User aggregate maintains consistency for:
- User profile information
- Account status and activation
- Email verification state
- Active authentication sessions
- Password and security settings

#### Business Invariants
1. **Email Uniqueness**: No two users can have the same email address
2. **Account Consistency**: User.isActive must match UserAccount.accountStatus
3. **Verification Consistency**: Account can only be active if email is verified
4. **Session Validity**: All active sessions must belong to an active user account
5. **Role Consistency**: User role must be valid and cannot be null

#### Aggregate Operations

| Operation | Description | Business Rules |
|-----------|-------------|----------------|
| registerUser() | Creates new user with account | Email must be unique, all required fields provided |
| activateAccount() | Activates user account after email verification | Email must be verified first |
| authenticateUser() | Validates credentials and creates session | Account must be active, password must match |
| updateProfile() | Updates user profile information | Only user can update their own profile |
| lockAccount() | Locks account due to security concerns | Can only lock active accounts |
| changePassword() | Changes user password | Must meet complexity requirements |
| terminateAllSessions() | Terminates all user sessions | Used for security purposes |

#### State Transitions

```
PendingVerification → Active (via email verification)
Active → Inactive (via admin action)
Active → Suspended (via policy violation)
Active → Locked (via security concerns)
Inactive → Active (via admin action)
Suspended → Active (via admin review)
Locked → Active (via security review)
```

### 2. EmailVerification Aggregate (Alternative Design)

In some cases, EmailVerification could be modeled as a separate aggregate if it needs to be managed independently.

#### Aggregate Root: EmailVerification Entity

#### Aggregate Boundaries
- Email verification tokens and their lifecycle
- Verification attempts and expiration
- Token generation and validation

#### Business Invariants
1. **Token Uniqueness**: Each verification token must be unique
2. **Single Active Token**: Only one active token per user email
3. **Expiration Consistency**: Expired tokens cannot be used
4. **Usage Consistency**: Used tokens cannot be reused

### Aggregate Design Decisions

#### Why User as Single Aggregate Root?
1. **Consistency**: User profile, account status, and authentication are tightly coupled
2. **Transactional Boundaries**: Most operations need to update multiple related entities
3. **Business Logic**: Authentication and profile management are core user operations
4. **Performance**: Reduces need for distributed transactions

#### Aggregate Size Considerations
- The User aggregate is appropriately sized for the domain
- EmailVerification and AuthenticationSession are managed as collections
- Each aggregate operation maintains consistency within the boundary
- Cross-aggregate operations use domain events for eventual consistency

#### Concurrency Control
- Optimistic locking on User aggregate root
- Version field to detect concurrent modifications
- Retry logic for concurrent update scenarios
- Event sourcing consideration for audit trail

## Repository Interfaces

Repository interfaces define the contract for data persistence and retrieval. They abstract the data access layer from the domain logic.

### 1. UserRepository Interface

Manages persistence of User aggregates.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| save() | User | User | Saves or updates a user aggregate |
| findById() | UUID | User | Finds user by unique identifier |
| findByEmail() | Email | User | Finds user by email address |
| findByEmployeeId() | EmployeeId | User | Finds user by employee ID |
| existsByEmail() | Email | Boolean | Checks if email already exists |
| existsByEmployeeId() | EmployeeId | Boolean | Checks if employee ID already exists |
| findByRole() | UserRole | List<User> | Finds all users with specific role |
| findActiveUsers() | - | List<User> | Finds all active users |
| delete() | UUID | Boolean | Soft deletes a user |

#### Query Specifications

| Specification | Parameters | Description |
|---------------|------------|-------------|
| ActiveUsersSpec | - | Specification for active users |
| UsersByRoleSpec | UserRole | Specification for users by role |
| UsersByDepartmentSpec | String | Specification for users by department |
| RecentlyCreatedUsersSpec | DateTime | Specification for recently created users |

### 2. EmailVerificationRepository Interface

Manages persistence of email verification entities.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| save() | EmailVerification | EmailVerification | Saves email verification |
| findByToken() | VerificationToken | EmailVerification | Finds verification by token |
| findByUserId() | UUID | List<EmailVerification> | Finds verifications for user |
| findActiveByUserId() | UUID | EmailVerification | Finds active verification for user |
| markAsUsed() | UUID | Boolean | Marks verification as used |
| deleteExpired() | DateTime | Integer | Deletes expired verifications |
| findExpiredTokens() | DateTime | List<EmailVerification> | Finds expired tokens |

### 3. AuthenticationSessionRepository Interface

Manages persistence of authentication sessions.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| save() | AuthenticationSession | AuthenticationSession | Saves authentication session |
| findByToken() | SessionToken | AuthenticationSession | Finds session by token |
| findByUserId() | UUID | List<AuthenticationSession> | Finds all sessions for user |
| findActiveSessions() | UUID | List<AuthenticationSession> | Finds active sessions for user |
| terminateSession() | UUID | Boolean | Terminates specific session |
| terminateAllUserSessions() | UUID | Integer | Terminates all user sessions |
| deleteExpiredSessions() | DateTime | Integer | Deletes expired sessions |
| findExpiredSessions() | DateTime | List<AuthenticationSession> | Finds expired sessions |

### 4. UserAccountRepository Interface

Manages persistence of user account entities.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| save() | UserAccount | UserAccount | Saves user account |
| findByUserId() | UUID | UserAccount | Finds account by user ID |
| findLockedAccounts() | - | List<UserAccount> | Finds all locked accounts |
| updateAccountStatus() | UUID, AccountStatus | Boolean | Updates account status |
| incrementFailedLogins() | UUID | Integer | Increments failed login count |
| resetFailedLogins() | UUID | Boolean | Resets failed login count |
| findAccountsToUnlock() | DateTime | List<UserAccount> | Finds accounts ready to unlock |

## Repository Implementation Guidelines

### 1. Transaction Management
- Each repository method should be transactional
- Aggregate consistency must be maintained within transactions
- Use optimistic locking for concurrent access control
- Implement retry logic for transient failures

### 2. Performance Considerations
- Implement caching for frequently accessed data
- Use database indexes on commonly queried fields
- Implement pagination for large result sets
- Consider read replicas for query-heavy operations

### 3. Error Handling
- Throw domain-specific exceptions for business rule violations
- Handle infrastructure exceptions appropriately
- Provide meaningful error messages
- Log errors for monitoring and debugging

### 4. Data Consistency
- Ensure referential integrity between related entities
- Implement soft deletes to maintain data history
- Use database constraints to enforce business rules
- Implement audit trails for sensitive operations

### 5. Security Considerations
- Never store plain text passwords
- Implement proper encryption for sensitive data
- Use parameterized queries to prevent SQL injection
- Implement access controls at the repository level

## Domain Model Interactions

This section documents the key workflows and interactions between domain components.

### 1. User Registration Workflow

#### Sequence of Operations

1. **Input Validation**
   - UserRegistrationService validates registration data
   - Email and EmployeeId value objects validate format
   - Check business rules (required fields, format validation)

2. **Uniqueness Check**
   - UserRepository.existsByEmail() checks email uniqueness
   - UserRepository.existsByEmployeeId() checks employee ID uniqueness
   - Throw exception if duplicates found

3. **User Creation**
   - Create User aggregate with profile information
   - Create UserAccount with PendingVerification status
   - Generate secure password hash using Password value object

4. **Email Verification Setup**
   - EmailVerificationService generates verification token
   - Create EmailVerification entity with token and expiration
   - Add to User aggregate

5. **Persistence**
   - UserRepository.save() persists the complete User aggregate
   - Transaction ensures consistency across all entities

6. **Event Publishing**
   - Publish UserRegistered domain event
   - Publish EmailVerificationRequested domain event

#### Interaction Diagram
```
Client → UserRegistrationService → UserRepository
                ↓
        EmailVerificationService → EmailVerification
                ↓
        DomainEventPublisher → [UserRegistered, EmailVerificationRequested]
```

### 2. Email Verification Workflow

#### Sequence of Operations

1. **Token Validation**
   - EmailVerificationService receives verification token
   - EmailVerificationRepository.findByToken() retrieves verification
   - VerificationToken value object validates format and expiration

2. **Business Rule Validation**
   - Check if token exists and is not used
   - Check if token is not expired
   - Verify token belongs to correct user

3. **Account Activation**
   - Update EmailVerification.isUsed = true
   - Update UserAccount.emailVerified = true
   - Update UserAccount.accountStatus = Active
   - Update User.isActive = true

4. **Persistence**
   - UserRepository.save() persists updated User aggregate
   - Transaction ensures consistency

5. **Event Publishing**
   - Publish EmailVerified domain event

#### Interaction Diagram
```
Client → EmailVerificationService → EmailVerificationRepository
                ↓
        User Aggregate → UserAccount (status update)
                ↓
        UserRepository → Database
                ↓
        DomainEventPublisher → [EmailVerified]
```

### 3. Authentication Workflow

#### Sequence of Operations

1. **Credential Validation**
   - AuthenticationService receives email and password
   - UserRepository.findByEmail() retrieves user
   - Password value object verifies hash against provided password

2. **Account Status Check**
   - Verify UserAccount.accountStatus is Active
   - Verify UserAccount.emailVerified is true
   - Check if account is not locked

3. **Session Creation**
   - Generate secure SessionToken
   - Create AuthenticationSession entity
   - Set session expiration time
   - Add session to User aggregate

4. **Failed Login Handling** (if authentication fails)
   - UserAccount.incrementFailedLogins()
   - Check if account should be locked (5 attempts)
   - Update UserAccount.accountLockedUntil if needed
   - Publish AccountLocked event if locked

5. **Successful Login**
   - Reset UserAccount.failedLoginAttempts to 0
   - Update User.lastLoginAt
   - UserRepository.save() persists changes

6. **Event Publishing**
   - Publish UserLoggedIn domain event (success)
   - Publish AccountLocked domain event (if locked)

#### Interaction Diagram
```
Client → AuthenticationService → UserRepository
                ↓
        Password.verify() → Boolean
                ↓
        AuthenticationSession (create) → SessionToken
                ↓
        UserRepository.save() → Database
                ↓
        DomainEventPublisher → [UserLoggedIn]
```

### 4. Profile Update Workflow

#### Sequence of Operations

1. **Authorization Check**
   - Verify user is updating their own profile
   - Validate session token is active and not expired

2. **Input Validation**
   - UserProfileService validates update data
   - Value objects validate individual fields
   - Check business rules for profile updates

3. **Special Handling for Email Changes**
   - If email is being changed, require re-verification
   - Create new EmailVerification for new email
   - Keep account active but mark email as unverified

4. **Profile Update**
   - Update User entity with new profile information
   - Update User.updatedAt timestamp
   - Maintain audit trail of changes

5. **Persistence**
   - UserRepository.save() persists updated User aggregate

6. **Event Publishing**
   - Publish UserProfileUpdated domain event
   - Publish EmailVerificationRequested (if email changed)

#### Interaction Diagram
```
Client → UserProfileService → UserRepository
                ↓
        Value Objects (validation) → Boolean
                ↓
        User Aggregate (update) → Profile Data
                ↓
        UserRepository.save() → Database
                ↓
        DomainEventPublisher → [UserProfileUpdated]
```

### 5. Session Management Workflow

#### Session Validation
1. AuthenticationService.validateSession() receives session token
2. AuthenticationSessionRepository.findByToken() retrieves session
3. Check session expiration and user account status
4. Update session.lastAccessedAt if valid
5. Return session validation result

#### Session Termination
1. AuthenticationService.terminateSession() receives session token
2. Mark AuthenticationSession.isActive = false
3. UserRepository.save() persists changes
4. Publish UserLoggedOut domain event

#### Automatic Session Cleanup
1. Background process finds expired sessions
2. AuthenticationSessionRepository.deleteExpiredSessions()
3. Publish UserLoggedOut events for expired sessions

### 6. Cross-Cutting Concerns

#### Error Handling
- Domain exceptions for business rule violations
- Infrastructure exceptions for technical failures
- Proper error propagation through service layers
- Meaningful error messages for client applications

#### Security
- Password hashing with secure algorithms
- Session token generation with cryptographic security
- Protection against timing attacks
- Rate limiting for authentication attempts

#### Audit and Monitoring
- Domain events provide audit trail
- Failed login attempt tracking
- Session activity monitoring
- Profile change tracking

#### Performance Optimization
- Caching of frequently accessed user data
- Efficient database queries with proper indexing
- Connection pooling for database access
- Asynchronous processing of domain events

## Validation Against User Stories

This section validates that the domain model fully supports the acceptance criteria for both user stories.

### US-SA-1: Solution Architect Account Creation

**User Story**: As a Solution Architect, I want to create an account in the system, so that I can register my skills and availability for customer opportunities.

#### Acceptance Criteria Validation

✅ **Solution Architect can access a registration page**
- Domain model supports user registration through UserRegistrationService
- UserRole enum includes SolutionArchitect value
- Registration workflow handles role-specific logic

✅ **Required fields include: name, email, employee ID, department, job title**
- User entity includes all required fields as mandatory attributes
- Value objects provide validation for email and employeeId
- UserRegistrationService validates all required fields are provided

✅ **System validates email format and uniqueness**
- Email value object validates format using RFC 5322 compliance
- UserRepository.existsByEmail() ensures uniqueness
- Registration fails if email already exists in system

✅ **System sends a verification email with account activation link**
- EmailVerificationService generates secure verification tokens
- EmailVerificationRequested domain event triggers email sending
- VerificationToken value object ensures secure token generation

✅ **Solution Architect receives confirmation upon successful registration**
- UserRegistered domain event can trigger confirmation notifications
- Registration workflow returns success confirmation
- User aggregate is persisted with PendingVerification status

✅ **Solution Architect can log in after account activation**
- Email verification workflow activates the account
- AuthenticationService validates account status before login
- Only Active accounts with verified emails can authenticate

### US-SM-1: Sales Manager Account Creation

**User Story**: As a Sales Manager, I want to create an account in the system, so that I can register customer opportunities and find matching Solution Architects.

#### Acceptance Criteria Validation

✅ **Sales Manager can access a registration page**
- Domain model supports user registration through UserRegistrationService
- UserRole enum includes SalesManager value
- Same registration workflow supports both roles

✅ **Required fields include: name, email, employee ID, department, job title**
- User entity includes all required fields as mandatory attributes
- Same validation logic applies regardless of user role
- UserRegistrationService handles role-agnostic field validation

✅ **System validates email format and uniqueness**
- Email value object provides consistent validation for all users
- UserRepository ensures email uniqueness across all roles
- Same business rules apply to all user types

✅ **System sends a verification email with account activation link**
- EmailVerificationService works consistently for all user roles
- Same verification token generation and validation logic
- EmailVerificationRequested event triggers for all users

✅ **Sales Manager receives confirmation upon successful registration**
- UserRegistered domain event includes role information
- Same confirmation mechanism for all user types
- Registration success handling is role-agnostic

✅ **Sales Manager can log in after account activation**
- AuthenticationService validates account regardless of role
- Same login workflow and session management for all users
- Role-based authorization handled at application layer

### Additional Business Rules Validation

#### Email Uniqueness Across Roles
✅ **Verified**: UserRepository.existsByEmail() checks uniqueness across all users regardless of role

#### Employee ID Uniqueness
✅ **Verified**: UserRepository.existsByEmployeeId() ensures employee IDs are unique across the system

#### Account Security
✅ **Verified**: Password value object enforces complexity requirements
✅ **Verified**: Account lockout mechanism prevents brute force attacks
✅ **Verified**: Session management provides secure authentication

#### Data Integrity
✅ **Verified**: User aggregate maintains consistency between User and UserAccount
✅ **Verified**: Email verification state is properly managed
✅ **Verified**: Business invariants are enforced at aggregate level

### Missing Requirements Analysis

After thorough analysis, the domain model covers all acceptance criteria for both user stories. No missing requirements identified.

### Extension Points

The domain model provides extension points for future requirements:

1. **Additional User Roles**: UserRole enum can be extended
2. **Enhanced Profile Fields**: User entity can accommodate additional fields
3. **Advanced Security**: Password policies can be enhanced
4. **Audit Requirements**: Domain events provide comprehensive audit trail
5. **Integration Points**: Repository interfaces support various persistence strategies

## Domain Model Summary

### Core Components Overview

The User Management Domain Model consists of the following key components:

#### Entities
1. **User** (Aggregate Root) - Core user identity and profile
2. **UserAccount** - Account status and authentication data
3. **EmailVerification** - Email verification process management
4. **AuthenticationSession** - User session management

#### Value Objects
1. **Email** - Email address validation and representation
2. **EmployeeId** - Employee identifier validation
3. **UserRole** - User role enumeration
4. **AccountStatus** - Account status enumeration
5. **Password** - Secure password handling
6. **VerificationToken** - Email verification token
7. **SessionToken** - Authentication session token

#### Domain Services
1. **UserRegistrationService** - User registration workflow
2. **EmailVerificationService** - Email verification process
3. **AuthenticationService** - Authentication and session management
4. **UserProfileService** - Profile management operations

#### Repository Interfaces
1. **UserRepository** - User aggregate persistence
2. **EmailVerificationRepository** - Email verification persistence
3. **AuthenticationSessionRepository** - Session persistence
4. **UserAccountRepository** - Account-specific operations

#### Domain Events
1. **UserRegistered** - New user registration
2. **EmailVerificationRequested** - Verification email needed
3. **EmailVerified** - Email successfully verified
4. **UserLoggedIn** - Successful authentication
5. **UserLoggedOut** - Session termination
6. **UserProfileUpdated** - Profile information changed
7. **AccountLocked** - Account locked due to security

### Design Principles Applied

#### Domain-Driven Design
- **Ubiquitous Language**: All components use business terminology
- **Bounded Context**: Clear boundaries for user management domain
- **Aggregate Design**: User aggregate maintains consistency
- **Rich Domain Model**: Business logic encapsulated in domain objects

#### SOLID Principles
- **Single Responsibility**: Each component has a focused purpose
- **Open/Closed**: Extensible through interfaces and events
- **Liskov Substitution**: Value objects are properly substitutable
- **Interface Segregation**: Repository interfaces are focused
- **Dependency Inversion**: Services depend on abstractions

#### Security by Design
- **Password Security**: Secure hashing and complexity requirements
- **Session Management**: Secure token generation and validation
- **Account Protection**: Lockout mechanisms and rate limiting
- **Data Validation**: Comprehensive input validation

### Business Rules Enforcement

The domain model enforces all critical business rules:

1. **Email Uniqueness**: Enforced at repository level
2. **Account Activation**: Required before authentication
3. **Password Complexity**: Enforced by Password value object
4. **Session Security**: Secure token generation and expiration
5. **Account Lockout**: Protection against brute force attacks
6. **Data Integrity**: Aggregate consistency maintained

### Integration Capabilities

The domain model provides clean integration points:

1. **Domain Events**: Enable loose coupling with other services
2. **Repository Interfaces**: Support multiple persistence strategies
3. **Service Interfaces**: Clear contracts for application layer
4. **Value Objects**: Reusable across domain boundaries

### Performance Considerations

The model includes performance optimization strategies:

1. **Aggregate Size**: Appropriately sized for consistency needs
2. **Caching Strategy**: Repository interfaces support caching
3. **Query Optimization**: Specific query methods for common operations
4. **Event Processing**: Asynchronous event handling capability

### Scalability Features

The domain model supports scalability requirements:

1. **Stateless Services**: Domain services are stateless
2. **Event-Driven Architecture**: Supports distributed processing
3. **Repository Abstraction**: Enables database scaling strategies
4. **Session Management**: Supports distributed session storage

### Conclusion

The User Management Domain Model successfully implements all requirements from user stories US-SA-1 and US-SM-1. It provides a robust, secure, and extensible foundation for user management and authentication services. The model follows Domain-Driven Design principles and incorporates security best practices while maintaining clean separation of concerns and high cohesion within domain boundaries.

The model is ready for implementation and can serve as the foundation for the User Management & Authentication Service in the Solution Architect Matching System.
