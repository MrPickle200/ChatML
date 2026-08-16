---
name: pydantic_and_fastapi_design
description: Design robust Pydantic models and FastAPI endpoints following production-grade API design principles.
---

# Skill: Design Pydantic Models and FastAPI APIs

## Purpose

Design robust Pydantic models and FastAPI endpoints following production-grade API design principles.

## Core Principles

### 1. Treat Endpoint Signatures as Contracts

Every FastAPI endpoint defines a contract:

* Request schemas specify what clients can send.
* Response schemas specify what clients receive.
* Validation is enforced automatically through Pydantic.
* OpenAPI documentation is generated from these contracts.

Never design endpoints without explicit request and response schemas.

---

### 2. Separate Models by Responsibility

Always use distinct models for:

#### Request Models

Used for inbound client data.

Example:

* UserCreate
* DocumentUploadRequest
* ChatRequest

Requirements:

* Accept only fields the client controls.
* Use `extra="forbid"` when appropriate.
* Add validation constraints.

#### Database Models

Used internally for persistence.

Example:

* UserDB
* DocumentDB

May contain:

* Internal IDs
* Permissions
* Metadata
* Audit fields
* Sensitive information

Never expose directly through APIs.

#### Response Models

Used for outbound API responses.

Example:

* UserResponse
* DocumentResponse

Requirements:

* Whitelist only fields intended for clients.
* Exclude secrets and internal metadata.
* Always use as FastAPI `response_model`.

---

### 3. Prefer Declarative Validation

Use Pydantic constraints whenever possible:

* min_length
* max_length
* gt / ge
* lt / le
* pattern
* Literal
* Enum
* EmailStr

Example:

```python
name: str = Field(min_length=3, max_length=100)
price: float = Field(gt=0)
```

Avoid manual validation inside route handlers unless business rules require it.

---

### 4. Use Validators for Business Invariants

Use:

* `@field_validator`

  * Single-field normalization and validation.

* `@model_validator`

  * Cross-field validation.

Examples:

* Normalize email addresses.
* Ensure start_date < end_date.
* Ensure either field A or field B is supplied.

---

### 5. Design Clear REST Endpoints

Follow REST conventions:

| Action                 | Method |
| ---------------------- | ------ |
| Create                 | POST   |
| Read                   | GET    |
| Update Entire Resource | PUT    |
| Partial Update         | PATCH  |
| Delete                 | DELETE |

Use nouns in URLs:

Good:

```text
POST /documents
GET /documents/{document_id}
```

Bad:

```text
POST /createDocument
GET /getDocument
```

---

### 6. Use Proper Status Codes

Examples:

* 200 OK
* 201 Created
* 204 No Content
* 400 Bad Request
* 401 Unauthorized
* 403 Forbidden
* 404 Not Found
* 409 Conflict
* 422 Validation Error

Always return semantically correct status codes.

---

### 7. Design Pagination for List Endpoints

For collection endpoints:

```python
GET /documents?page=1&page_size=20
```

or cursor-based pagination for large datasets.

Always enforce a maximum page size.

---

### 8. Protect Sensitive Data

Never expose:

* passwords
* password hashes
* tokens
* API keys
* internal permissions
* tenant identifiers

Always expose data through dedicated response schemas.

---

### 9. Strong Typing Everywhere

Prefer:

```python
list[str]
dict[str, Any]
UUID
datetime
EmailStr
Literal
Enum
```

Avoid:

```python
dict
list
Any
```

unless absolutely necessary.

---

### 10. FastAPI Route Template

```python
@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    return await service.create_document(payload)
```

Requirements:

* Typed request model.
* Typed response model.
* Dependency injection.
* Business logic delegated to service layer.
* No database logic inside route handlers.

---

## Output Expectations

When asked to design an API:

1. Define request schema(s).
2. Define response schema(s).
3. Define validation constraints.
4. Define endpoint signatures.
5. Specify status codes.
6. Separate router, service, and repository concerns.
7. Prevent data leakage through response models.
8. Follow FastAPI and Pydantic v2 best practices.
9. Generate production-ready code rather than tutorial-style examples.
