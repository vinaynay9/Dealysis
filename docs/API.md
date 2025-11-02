# Dealysis API Documentation

This document describes the API endpoints available in the Dealysis application.

## Base URL

Development: `http://localhost:5173/api`
Production: `https://your-domain.com/api`

## Authentication

All API endpoints (except auth endpoints) require authentication via session cookies set by Auth.js.

The session is validated using the `auth()` function from `@/auth.js`.

### Headers
```
Cookie: authjs.session-token=<session-token>
```

---

## Endpoints

### Authentication

#### POST `/api/auth/signin`
Sign in with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

#### POST `/api/auth/signup`
Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "User Name" // optional
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

---

### Document Processing

#### POST `/api/process-documents`
Upload and analyze a document with AI.

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: File to upload (PDF, DOCX, DOC, TXT, CSV)
- `fileType`: `"reference"` or `"example"`

**Limits:**
- Max file size: 50MB
- Max analyzed text: 25,000 characters

**Response (Success):**
```json
{
  "success": true,
  "fileName": "pitch_deck.pdf",
  "fileType": "reference",
  "originalSize": 1024000,
  "analysis": "Extracted information about company...",
  "timestamp": "2024-01-01T00:00:00Z",
  "analysisType": "Content Analysis",
  "textLength": 50000,
  "analyzedLength": 25000
}
```

**Response (Error):**
```json
{
  "error": "File too large: 75MB. Maximum size is 50MB."
}
```

**Errors:**
- 400: Invalid file type, file too large, cannot extract text
- 500: AI analysis failed

---

### Memo Generation

#### POST `/api/generate-memo-sections`
Generate a specific section of an investment memo.

**Authentication:** Required

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "templateAnalysis": [
    {
      "fileName": "example_memo.pdf",
      "analysis": "Template structure analysis..."
    }
  ],
  "contentAnalyses": [
    {
      "fileName": "pitch_deck.pdf",
      "analysis": "Company information..."
    }
  ],
  "additionalContext": "Company is Series B SaaS startup...",
  "referenceTexts": [
    {
      "label": "Meeting Notes",
      "content": "Discussion with founder..."
    }
  ],
  "referenceUrls": [
    {
      "label": "Company Website",
      "url": "https://example.com"
    }
  ],
  "sectionToGenerate": "executive_summary"
}
```

**Valid Section Names:**
- `executive_summary`
- `company_overview`
- `market_opportunity`
- `product_technology`
- `competitive_landscape`
- `traction_financials`
- `team_leadership`
- `risks_recommendation`

**Response (Success):**
```json
{
  "success": true,
  "section": "executive_summary",
  "title": "Executive Summary",
  "content": "## Executive Summary\n\n### Overview\n...",
  "timestamp": "2024-01-01T00:00:00Z",
  "contextLength": 15000
}
```

**Response (Error):**
```json
{
  "error": "Failed to generate Executive Summary: AI service timeout",
  "section": "executive_summary"
}
```

**Errors:**
- 400: Invalid section name
- 429: AI service rate limit exceeded
- 500: Generation failed

---

### User Memos

#### GET `/api/user-memos`
Get all memos for the authenticated user.

**Authentication:** Required

**Query Parameters:**
- `search` (optional): Search term for title, company, or content
- `sortBy` (optional): Sort field (`created_at`, `updated_at`, `title`) - default: `updated_at`
- `limit` (optional): Max results - default: 50

**Response:**
```json
{
  "success": true,
  "memos": [
    {
      "id": "uuid",
      "title": "Acme Corp - Investment Memo",
      "company_name": "Acme Corp",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-02T00:00:00Z",
      "is_favorite": false,
      "preview": "## Executive Summary\n\nAcme Corp is a Series B..."
    }
  ]
}
```

#### GET `/api/user-memos/{id}`
Get a specific memo by ID.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "memo": {
    "id": "uuid",
    "title": "Acme Corp - Investment Memo",
    "company_name": "Acme Corp",
    "content": "Full memo content...",
    "sections": {
      "executive_summary": {
        "title": "Executive Summary",
        "content": "...",
        "timestamp": "2024-01-01T00:00:00Z"
      }
    },
    "metadata": {
      "generated": "2024-01-01T00:00:00Z",
      "totalSections": 8,
      "referenceMaterials": 5
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z",
    "is_favorite": false
  }
}
```

#### POST `/api/user-memos`
Create a new memo.

**Authentication:** Required

**Request Body:**
```json
{
  "title": "Acme Corp - Investment Memo",
  "company_name": "Acme Corp",
  "content": "Full memo markdown content...",
  "sections": {
    "executive_summary": {
      "title": "Executive Summary",
      "content": "...",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  },
  "metadata": {
    "generated": "2024-01-01T00:00:00Z",
    "totalSections": 8,
    "referenceMaterials": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "memo": {
    "id": "uuid",
    "title": "Acme Corp - Investment Memo",
    "company_name": "Acme Corp",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### PUT `/api/user-memos/{id}`
Update an existing memo.

**Authentication:** Required

**Request Body:** Same as POST

**Response:** Same as POST

#### DELETE `/api/user-memos/{id}`
Delete a memo.

**Authentication:** Required

**Response:**
```json
{
  "success": true
}
```

---

### Usage Tracking

#### POST `/api/track-usage`
Track memo generation usage and analytics.

**Authentication:** Optional (tracks anonymous sessions)

**Request Body:**
```json
{
  "company_name": "Acme Corp",
  "files_uploaded_count": 3,
  "reference_texts_count": 1,
  "reference_urls_count": 2,
  "company_context": "Series B SaaS startup...",
  "user_notes": null,
  "processing_time_seconds": 45,
  "sections_generated": 8,
  "generation_successful": true,
  "user_session_id": "session_1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "id": "uuid"
}
```

---

### Media Upload

#### POST `/api/upload-media`
Upload media files (images, videos, charts) for memo enrichment.

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Media file to upload
- `mediaType`: Type of media (`"image"`, `"video"`, `"document"`)
- `caption` (optional): Description or caption
- `sectionId` (optional): Associated memo section

**Response:**
```json
{
  "success": true,
  "url": "https://cdn.example.com/media/abc123.png",
  "fileName": "chart.png",
  "mimeType": "image/png",
  "mediaType": "image",
  "caption": "Revenue growth chart"
}
```

---

## AI Integration

### Internal Endpoint

The application uses an internal ChatGPT integration endpoint:

```
POST /integrations/chat-gpt/conversationgpt4
```

**Request:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert VC analyst..."
    },
    {
      "role": "user",
      "content": "Analyze this company..."
    }
  ],
  "stream": true // optional
}
```

**Response (Non-streaming):**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Based on the provided information..."
      }
    }
  ]
}
```

**Response (Streaming):**
Server-sent events (SSE) with chunks of the response.

---

## Error Handling

All endpoints return errors in the following format:

```json
{
  "error": "Human-readable error message",
  "details": "Technical details (optional)"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request (validation error, invalid input)
- `401`: Unauthorized (not authenticated)
- `403`: Forbidden (not authorized for this resource)
- `404`: Not found
- `413`: Payload too large
- `429`: Rate limit exceeded
- `500`: Internal server error

---

## Rate Limiting

Currently, there is **NO rate limiting** implemented on AI endpoints, which could lead to:
- High API costs
- Resource exhaustion
- Abuse potential

**Recommendation:** Implement rate limiting with Redis or similar.

---

## Best Practices

1. **Always check error responses** and handle them gracefully
2. **Set proper timeouts** for API calls (AI endpoints can be slow)
3. **Use streaming** for long-running AI operations
4. **Validate inputs** on the client before sending to API
5. **Handle authentication errors** and redirect to login
6. **Show progress indicators** for file uploads and memo generation
7. **Implement retry logic** for transient failures (especially AI APIs)

---

## Development & Testing

### Testing with curl

```bash
# Login
curl -X POST http://localhost:5173/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c cookies.txt

# Upload document
curl -X POST http://localhost:5173/api/process-documents \
  -F "file=@pitch_deck.pdf" \
  -F "fileType=reference" \
  -b cookies.txt

# Generate memo section
curl -X POST http://localhost:5173/api/generate-memo-sections \
  -H "Content-Type: application/json" \
  -d '{"contentAnalyses":[...], "sectionToGenerate":"executive_summary"}' \
  -b cookies.txt
```

---

## Future API Improvements

1. **OpenAPI/Swagger specification** for auto-generated docs
2. **Versioning** (`/api/v1/...`) for backwards compatibility
3. **Rate limiting** to prevent abuse
4. **WebSocket support** for real-time memo updates
5. **Bulk operations** (upload multiple files at once)
6. **Webhooks** for async operations
7. **Better error codes** with machine-readable error types
8. **Request validation** with Zod schemas
9. **Response pagination** for large result sets
10. **API key authentication** for programmatic access

