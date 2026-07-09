# Candidate Authentication Backend

This is the candidate registration and login backend for the **Online Exam Monitoring & Integrity Analytics Platform**, implemented in Python using Flask and SQLite.

---

## Folder Structure

```
backend/
│
├── app.py              # Main Flask application entry point
├── auth.py             # Authentication routes blueprint (login, registration)
├── database.py         # Database connection helpers & parameterized SQLite queries
├── models.py           # Candidate domain model mappings
├── config.py           # Application configurations (database path, keys)
├── requirements.txt    # List of project dependencies
│
├── templates/          # HTML form templates for manual testing
│   ├── login.html      # Candidate login form
│   └── register.html   # Candidate registration form
│
└── README.md           # Documentation (this file)
```

---

## Project Setup & Installation

### 1. Prerequisites
- **Python 3.12+** installed on your local system.

### 2. Create and Activate a Virtual Environment
In your terminal, navigate to the `backend/` directory:

```bash
cd backend
python -m venv venv
```

**Activate it on Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Activate it on Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the Flask server by running:
```bash
python app.py
```
By default, the application will bind to `http://127.0.0.1:5000/` in debug mode.

---

## API Endpoints

### 1. Register Candidate
- **Endpoint**: `/auth/register`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "securepassword123"
  }
  ```
- **Validation Constraints**:
  - Name, email, and password are required.
  - Email format must be valid (e.g., `user@domain.com`).
  - Password must be at least **8 characters** long.
- **Success Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Candidate registered successfully",
    "candidate_id": 1
  }
  ```
- **Error Responses**:
  - **400 Bad Request** (Validation Error):
    ```json
    {
      "status": "error",
      "message": "Validation failed: Password must be at least 8 characters long."
    }
    ```
  - **409 Conflict** (Duplicate Email):
    ```json
    {
      "status": "error",
      "message": "Email already exists"
    }
    ```

### 2. Login Candidate
- **Endpoint**: `/auth/login`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "securepassword123"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Login successful",
    "candidate": {
      "candidate_id": 1,
      "name": "Jane Doe",
      "email": "jane@example.com",
      "photo_path": null,
      "created_at": "2026-07-09T08:14:00"
    }
  }
  ```
- **Error Responses**:
  - **404 Not Found** (Candidate not registered):
    ```json
    {
      "status": "error",
      "message": "User not found"
    }
    ```
  - **401 Unauthorized** (Incorrect credentials):
    ```json
    {
      "status": "error",
      "message": "Invalid credentials"
    }
    ```

---

## Testing Instructions

### Option A: Using Web Browser UI
1. Start the Flask application.
2. Open your web browser and navigate to `http://127.0.0.1:5000/`.
3. You will be redirected to the Login page. Click the "Register here" link to go to the Register page.
4. Input details and register. You will see success/error notifications displayed on screen.
5. Log in with your registered credentials.

### Option B: Using cURL (PowerShell / Terminal)
Open a new terminal window while the server is running and run the following tests:

1. **Register a new candidate**:
   ```powershell
   curl.exe -X POST -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "john@example.com", "password": "mypassword123"}' http://127.0.0.1:5000/auth/register
   ```
2. **Attempt registering same candidate (Duplicate Check)**:
   ```powershell
   curl.exe -X POST -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "john@example.com", "password": "mypassword123"}' http://127.0.0.1:5000/auth/register
   ```
3. **Login with correct credentials**:
   ```powershell
   curl.exe -X POST -H "Content-Type: application/json" -d '{"email": "john@example.com", "password": "mypassword123"}' http://127.0.0.1:5000/auth/login
   ```
4. **Login with incorrect password**:
   ```powershell
   curl.exe -X POST -H "Content-Type: application/json" -d '{"email": "john@example.com", "password": "wrongpassword"}' http://127.0.0.1:5000/auth/login
   ```
