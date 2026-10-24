# FastAPI Authentication and Rate Limiting API

A REST API built with **FastAPI** that implements user registration, secure password hashing, JWT-based authentication, protected endpoints, and rate limiting. This project focuses on backend fundamentals, API security, and automated testing.

## Features

- **User Registration** — Register users with email validation and password length checks.
- **Password Security** — Store hashed passwords instead of plain-text passwords.
- **JWT Authentication** — Authenticate users and issue access tokens.
- **Protected Endpoints** — Restrict access to authenticated users using bearer tokens.
- **Rate Limiting** — Limit requests per client IP and return `429 Too Many Requests` when the limit is exceeded.
- **Input Validation** — Validate request data using Pydantic.
- **API Documentation** — Explore and test endpoints using Swagger UI.
- **Automated Testing** — Test authentication behavior and rate-limiting functionality with pytest.
- **Database Integration** — Use SQLite with SQLAlchemy ORM.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API framework |
| SQLite | Database |
| SQLAlchemy | Database ORM |
| Pydantic | Request validation and settings |
| JWT | Token-based authentication |
| Argon2 password hashing | Secure password storage |
| Pytest | Automated testing |
| Swagger UI | Interactive API documentation |

## Project Structure

```text
auth-rate-limit-api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models.py
│   ├── rate_limit.py
│   ├── schemas.py
│   ├── security.py
│   └── routers/
│       ├── __init__.py
│       └── auth.py
├── tests/
│   ├── test_auth.py
│   └── test_rate_limit.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Harshal2605-M/authentication_and_rate_limiting_using_fastapi.git
cd authentication_and_rate_limiting_using_fastapi
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the environment's Python executable directly instead.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using `.env.example` as a reference.

Generate a secure JWT secret:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `.env`, using the variable names defined in `app/config.py` and `.env.example`.

Example:

```dotenv
JWT_SECRET_KEY=replace-with-your-generated-secret
```

Keep your actual `.env` file private. Never commit real secrets to GitHub.

### 5. Start the development server

```powershell
uvicorn app.main:app --reload
```

The API will be available locally at:

- **API base URL:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

The SQLite database is configured by the application and is typically created locally when the application initializes its tables.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Authenticate and obtain a JWT |
| GET | `/users/me` | Retrieve the authenticated user's profile |

### 1. Health Check

**Request**

```http
GET /health
```

**Example response**

```json
{
  "status": "healthy"
}
```

### 2. Register a User

**Request**

```http
POST /auth/register
Content-Type: application/json
```

**Example request body**

```json
{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

A successful registration returns the user ID and email. The password is not returned.

Common responses:

- `201 Created` — User registered successfully.
- `409 Conflict` — Email already registered.
- `422 Unprocessable Entity` — Invalid request data.

### 3. Login

The login endpoint uses OAuth2 password form data.

**Request**

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

**Form fields**

```text
username=user@example.com
password=StrongPass123
```

Although the application uses an email address, the OAuth2 form field is named `username`.

**Example response**

```json
{
  "access_token": "<jwt-access-token>",
  "token_type": "bearer"
}
```

Common responses:

- `200 OK` — Authentication successful.
- `401 Unauthorized` — Invalid credentials.
- `422 Unprocessable Entity` — Missing or invalid form fields.

### 4. Access the Protected Profile

Include the access token in the `Authorization` header.

**Request**

```http
GET /users/me
Authorization: Bearer <jwt-access-token>
```

**Example response**

```json
{
  "id": 1,
  "email": "user@example.com"
}
```

Common responses:

- `200 OK` — Valid token and authenticated user.
- `401 Unauthorized` — Missing, invalid, or expired token.

## Rate Limiting

The API uses middleware to check incoming requests before allowing them to reach application endpoints.

The current implementation is configured for **5 requests per client IP within a 60-second sliding window**.

When a client exceeds the limit, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

The exact retry duration depends on the request history.

Example response body:

```json
{
  "detail": "Too many requests. Please try again later."
}
```

Health checks and Swagger documentation paths are excluded from rate limiting.

### Current Limitations

- Request counters are stored in application memory.
- Counters reset when the application restarts.
- Counters are not shared across multiple application workers.
- Multiple users sharing an IP address also share the same counter.
- A production deployment would benefit from a shared rate-limiting store such as Redis and appropriate trusted-proxy configuration.

## Running Tests

Run the authentication tests:

```powershell
python -m pytest tests/test_auth.py -v
```

Run the rate-limiting tests:

```powershell
python -m pytest tests/test_rate_limit.py -v
```

Run the complete test suite:

```powershell
python -m pytest -v
```

The tests cover registration, duplicate registration, invalid login credentials, protected endpoint access, request limits, retry headers, and excluded health checks.

Authentication tests use a separate temporary SQLite database to avoid modifying the local application database.

## Security Considerations

- Passwords are stored as hashes rather than plain text.
- JWT signing secrets are loaded from environment configuration.
- Protected endpoints validate bearer tokens before returning user information.
- Access tokens have a configured expiration time.
- Invalid login credentials return a generic error message.
- Environment files and local databases should remain excluded from version control.

This is a learning and development project. Before production use, review authentication abuse protections, token revocation requirements, rate-limiting storage, database migrations, logging, HTTPS, and deployment configuration.

## Future Improvements

- Add comprehensive successful-login and JWT validation tests.
- Add refresh-token support and token revocation if required.
- Introduce Redis-backed distributed rate limiting.
- Add database migrations with Alembic.
- Add CI with GitHub Actions.
- Improve logging and error handling.
- Integrate the authentication functionality into the MLPilot application.

## Author

**Harshal Mahajan**

GitHub: [Harshal2605-M](https://github.com/Harshal2605-M)

Repository: [Authentication and Rate Limiting Using FastAPI](https://github.com/Harshal2605-M/authentication_and_rate_limiting_using_fastapi)
