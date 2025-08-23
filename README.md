# Parachute Portal API - Authentication Service

A secure FastAPI-based authentication service with JWT token management, user registration, and role-based access control.

## 🚀 Features

- **Secure User Authentication** with JWT tokens
- **Email-based Registration** with allowed email validation
- **Password Hashing** using bcrypt
- **Role-based Access Control** (Staff/Admin)
- **PostgreSQL Database** with SQLAlchemy ORM
- **Comprehensive API Documentation** with FastAPI auto-docs
- **CORS Support** for cross-origin requests

## 🏗️ Architecture

```
Parachute_Portal/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration and environment settings
├── models/                # Database and Pydantic models
├── routers/               # API route definitions
├── services/              # Business logic and utilities
├── alembic/               # Database migration management
└── requirements.txt       # Python dependencies
```

## 🛠️ Technology Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Database Migrations**: Alembic
- **Validation**: Pydantic models
- **API Documentation**: FastAPI auto-generated docs

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- Redis (optional, for future features)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Parachute_Portal
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```env
# JWT Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
POSTGRESQL_DB=postgresql://username:password@localhost:5432/database_name

# Optional: Redis
REDIS_URL=redis://localhost:6379/0
```

### 5. Database Setup
```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Run migrations
alembic upgrade head
```

### 6. Run the Application
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the application is running, you can access:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 🔐 Authentication Endpoints

### Base URL
```
http://localhost:8000/auth
```

### 1. User Registration
**Endpoint**: `POST /auth/signup`

**Description**: Register a new user. The email must be in the allowed emails list.

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@company.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john.doe@company.com",
    "is_active": true,
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Postman Example**:
```
Method: POST
URL: http://localhost:8000/auth/signup
Headers: 
  Content-Type: application/json
Body (raw JSON):
{
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@company.com",
  "password": "securepassword123"
}
```

### 2. User Login
**Endpoint**: `POST /auth/login`

**Description**: Authenticate user and receive JWT token.

**Request Body**:
```json
{
  "email": "john.doe@company.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Postman Example**:
```
Method: POST
URL: http://localhost:8000/auth/login
Headers: 
  Content-Type: application/json
Body (raw JSON):
{
  "email": "john.doe@company.com",
  "password": "securepassword123"
}
```

### 3. Get Current User Info
**Endpoint**: `GET /auth/me`

**Description**: Retrieve current authenticated user information.

**Headers**:
```
Authorization: Bearer <your-jwt-token>
```

**Response**:
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@company.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Postman Example**:
```
Method: GET
URL: http://localhost:8000/auth/me
Headers: 
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Update User Information
**Endpoint**: `PUT /auth/me`

**Description**: Update current user information.

**Headers**:
```
Authorization: Bearer <your-jwt-token>
```

**Request Body** (all fields optional):
```json
{
  "first_name": "Johnny",
  "last_name": "Smith",
  "username": "johnnysmith",
  "email": "johnny.smith@company.com",
  "password": "newpassword123"
}
```

**Response**:
```json
{
  "id": 1,
  "first_name": "Johnny",
  "last_name": "Smith",
  "username": "johnnysmith",
  "email": "johnny.smith@company.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Postman Example**:
```
Method: PUT
URL: http://localhost:8000/auth/me
Headers: 
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  Content-Type: application/json
Body (raw JSON):
{
  "first_name": "Johnny",
  "last_name": "Smith",
  "username": "johnnysmith",
  "email": "johnny.smith@company.com"
}
```

### 5. User Logout
**Endpoint**: `POST /auth/logout`

**Description**: Logout user (client should discard the token).

**Headers**:
```
Authorization: Bearer <your-jwt-token>
```

**Response**:
```json
{
  "message": "Successfully logged out"
}
```

**Postman Example**:
```
Method: POST
URL: http://localhost:8000/auth/logout
Headers: 
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🗄️ Database Models

### User Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### AllowedEmail Table
```sql
CREATE TABLE allowed_emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'staff',
    is_registered BOOLEAN DEFAULT FALSE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔒 Security Features

### JWT Token Configuration
- **Algorithm**: HS256
- **Default Expiry**: 30 minutes (configurable)
- **Secret Key**: Environment variable (JWT_SECRET_KEY)

### Password Security
- **Hashing Algorithm**: bcrypt
- **Minimum Length**: 8 characters
- **Salt Rounds**: Automatic

### Access Control
- **Email Validation**: Only pre-approved emails can register
- **Token-based Authentication**: JWT tokens for API access
- **Role-based Permissions**: Staff and Admin roles

## 📝 Pydantic Models

### UserCreate
```python
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
```

### UserLogin
```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

### UserUpdate
```python
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
```

### UserResponse
```python
class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

## 🚨 Error Handling

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (validation errors, duplicate email, etc.)
- **401**: Unauthorized (invalid credentials, missing token)
- **403**: Forbidden (insufficient permissions)
- **500**: Internal Server Error

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT signing | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | 30 |
| `POSTGRESQL_DB` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive API testing.

## 🔍 Audit Logging

The Parachute Portal API includes comprehensive audit logging for HIPAA compliance and security monitoring. All user actions are automatically logged with detailed information including user identity, IP address, user agent, and action details.

### Audit Log Structure

Each audit log entry contains:
- **User Information**: User ID and first name
- **Action Category**: Type of action performed
- **Action Details**: Detailed description of the action
- **Resource Context**: Table name and record ID affected
- **Security Information**: IP address and user agent
- **Timestamp**: When the action occurred

### Available Action Categories

- `authentication` - Login/logout attempts
- `user_management` - User creation, updates, deletion
- `data_access` - Profile access, data viewing
- `system_admin` - Admin actions
- `security_event` - Security-related events
- `compliance` - Compliance-related actions

### Admin Audit Endpoints

#### 1. Get All Audit Logs (Paginated)
```http
GET /admin/audit-logs
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `limit` (optional): Number of logs per page (default: 100)
- `page` (optional): Page number (default: 1)

**Response:**
```json
{
    "logs": [
        {
            "id": 1,
            "user": "John",
            "category": "authentication",
            "action_details": "User john@company.com successfully logged in",
            "ip_address": "127.0.0.1",
            "user_agent": "PostmanRuntime/7.45.0",
            "created_at": "2025-08-21T19:30:55.256000"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_count": 450,
        "limit": 100,
        "has_next": true,
        "has_prev": false
    }
}
```

#### 2. Filter Audit Logs by Type
```http
GET /admin/audit-logs/type/{category}
Authorization: Bearer {admin_token}
```

**Path Parameters:**
- `category`: Action category to filter by

**Query Parameters:**
- `limit` (optional): Number of logs per page (default: 100)
- `page` (optional): Page number (default: 1)

**Example:**
```http
GET /admin/audit-logs/type/authentication?limit=50&page=2
```

#### 3. Filter Audit Logs by User
```http
GET /admin/audit-logs/user/{user_id}
Authorization: Bearer {admin_token}
```

**Path Parameters:**
- `user_id`: ID of the user to filter by

**Query Parameters:**
- `limit` (optional): Number of logs per page (default: 100)
- `page` (optional): Page number (default: 1)

**Example:**
```http
GET /admin/audit-logs/user/1?limit=25
```

#### 4. Combined Filter (Type + User)
```http
GET /admin/audit-logs/filter
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `category` (optional): Action category to filter by
- `user_id` (optional): User ID to filter by
- `limit` (optional): Number of logs per page (default: 100)
- `page` (optional): Page number (default: 1)

**Example:**
```http
GET /admin/audit-logs/filter?category=authentication&user_id=1&limit=50&page=1
```

### Audit Log Creation

Audit logs are automatically created for:
- User authentication (login/logout)
- User management operations
- Data access and modifications
- Admin actions
- Security events

**Example Audit Log Creation:**
```python
DatabaseService.create_audit_log(
    db=db,
    user_id=user.id,
    category="authentication",
    action_details="User successfully logged in",
    resource_type="users",
    resource_id=user.id,
    request=request
)
```

### Security Features

- **IP Address Tracking**: Records client IP addresses
- **User Agent Logging**: Tracks browser/client information
- **Resource Context**: Links actions to specific database records
- **Admin Access Control**: Only admin users can access audit logs
- **Comprehensive Coverage**: All user actions are logged

## 🚀 Future Features

- [ ] Password reset functionality
- [ ] Email verification
- [ ] Two-factor authentication
- [ ] Session management
- [ ] Rate limiting

## 📞 Support

For questions or issues, please refer to the project documentation or contact the development team.

## 📄 License

This project is proprietary and confidential.
