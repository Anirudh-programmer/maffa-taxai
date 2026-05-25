# TaxAI API Reference

Base URL: `http://localhost:8000/api/v1`

All authenticated endpoints require the header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Authentication

### POST /auth/register
Register a new user with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "full_name": "Rahul Sharma",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "email": "user@example.com", ... }
}
```

---

### POST /auth/login
Login with email and password.

**Request:**
```json
{ "email": "user@example.com", "password": "securepassword123" }
```

---

### POST /auth/clerk/sync
Sync a Clerk session token and get a backend JWT.

**Request:**
```json
{ "clerk_token": "<clerk_session_token>" }
```

---

## Tax Calculator

### POST /tax/calculate
Calculate income tax for both old and new regimes.

**Request:**
```json
{
  "basic_salary": 600000,
  "hra_received": 120000,
  "other_allowances": 60000,
  "rent_paid": 120000,
  "city_type": "metro",
  "section_80c": 150000,
  "section_80ccd_nps": 50000,
  "section_80d": 25000,
  "home_loan_interest": 0,
  "age": 30,
  "financial_year": "2024-25"
}
```

**Response:**
```json
{
  "old_regime": {
    "gross_income": 780000,
    "total_deductions": 347400,
    "taxable_income": 432600,
    "total_tax": 18780,
    "effective_rate": 2.41,
    "take_home_monthly": 63435
  },
  "new_regime": {
    "gross_income": 780000,
    "total_deductions": 77400,
    "taxable_income": 702600,
    "total_tax": 37520,
    "effective_rate": 4.81,
    "take_home_monthly": 61874
  },
  "recommended_regime": "old",
  "tax_saved": 18740,
  "savings_percentage": 49.9,
  "key_recommendations": [...]
}
```

---

## Chat

### POST /chat/stream
Stream AI chat responses (Server-Sent Events).

**Request:**
```json
{
  "content": "Which tax regime is better for me?",
  "session_id": null,
  "document_ids": [],
  "use_rag": true
}
```

**SSE Events:**
```
data: {"type": "session_id", "session_id": "abc123"}
data: {"type": "chunk", "content": "Based on your..."}
data: {"type": "done", "session_id": "abc123"}
```

---

### GET /chat/sessions
List all chat sessions for the current user.

### GET /chat/sessions/{session_id}/messages
Get all messages in a session.

### DELETE /chat/sessions/{session_id}
Soft-delete a session.

---

## Documents

### POST /documents/upload
Upload a tax document (multipart/form-data).

**Form fields:**
- `file`: The PDF/image file
- `document_type`: `form_16` | `salary_slip` | `itr` | `investment_proof` | `other`

**Response:**
```json
{
  "id": "...",
  "filename": "...",
  "document_type": "form_16",
  "status": "processing",
  "extracted_data": null
}
```

---

### GET /documents/{document_id}/analysis
Get AI analysis of an uploaded document.

**Response:**
```json
{
  "status": "processed",
  "document_type": "form_16",
  "financial_year": "2023-24",
  "extracted_data": {
    "employer_name": "...",
    "total_income": 780000,
    "summary": "...",
    "key_observations": [...],
    "tax_saving_opportunities": [...]
  }
}
```

---

## Users

### GET /users/me
Get current user profile.

### PUT /users/me
Update user profile.

### GET /users/me/dashboard
Get dashboard statistics.

**Response:**
```json
{
  "total_chats": 12,
  "total_documents": 3,
  "total_calculations": 5,
  "estimated_tax_savings": 45000,
  "current_financial_year": "2024-25",
  "recommended_regime": "old"
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "error": "Error type",
  "detail": "Human-readable message"
}
```

Common status codes:
- `400` Bad Request — invalid input
- `401` Unauthorized — missing or invalid token
- `403` Forbidden — insufficient permissions
- `404` Not Found — resource doesn't exist
- `422` Unprocessable Entity — validation error
- `429` Too Many Requests — rate limit exceeded
- `500` Internal Server Error — unexpected error
