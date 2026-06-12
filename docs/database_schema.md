# Database Schema

## Overview

### MongoDB

Collections:

1. datasets
2. documents
3. conversations
4. messages
5. feedback

### Qdrant

Collection:

- learning_assistant

---

# datasets

Thông tin về một bộ tài liệu.

## Example

```json
{
  "_id": "dataset_001",
  "name": "MIT Calculus",
  "description": "Single Variable Calculus Notes",
  "status": "active",
  "created_at": "2026-06-08T10:00:00Z",
  "updated_at": "2026-06-08T10:00:00Z"
}
```

## Fields

| Field | Type | Description |
|---------|---------|---------|
| _id | ObjectId | Dataset ID |
| name | string | Dataset name |
| description | string | Dataset description |
| status | string | active/deleted |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

---

# documents

Một file thuộc dataset.

## Example

```json
{
  "_id": "doc_001",
  "dataset_id": null, // tạm thời để null
  "filename": "lecture_1.pdf",
  "file_type": "pdf",
  "file_size_bytes":12345,
  "version": 1,
  "status": "indexed",
  "created_at": "2026-06-08T10:05:00Z",
  "updated_at": "2026-06-08T10:05:00Z",
  "storage" : {
    "provider" : "local",
    "uri" : "..."
  }
}
```

## Fields

| Field | Type | Description |
|---------|---------|---------|
| _id | ObjectId | Document ID |
| dataset_id | ObjectId | Parent dataset |
| filename | string | File name |
| file_type | string | pdf/docx/txt |
| file_size_bytes | int | file size in bytes |
| version | int | Version number |
| status | string | uploaded/indexed/failed |
| created_at | datetime | Upload time |
| updated_at | datetime | Update time |
| storage | json | Storage path |

---

# conversations

Một cuộc hội thoại.

## Example

```json
{
  "_id": "conv_001",
  "title": "Backpropagation Discussion",
  "created_at": "2026-06-08T15:00:00Z",
  "updated_at": "2026-06-08T15:00:00Z"
}
```

## Fields

| Field | Type |
|-------|------|
| _id  | ObjectId |
| title | String |
| created_at | datetime |
| updated_at | datetime |


---

# messages

Tin nhắn trong hội thoại.

## Example

```json
{
  "_id": "msg_001",
  "conversation_id": "conv_001",
  "role": "user",
  "content": "What is backpropagation?",
  "sources": ["lecture1.pdf", "lecture2.pdf"],
  "created_at": "2026-06-08T15:01:00Z"
}
```

## Fields

| Field | Type |
|---------|---------|
| _id | ObjectId |
| conversation_id | ObjectId |
| role | string |
| content | string |
| sources | list[string] |
| created_at | datetime |

---

# feedback

Feedback từ người dùng.

## Example

```json
{
  "_id": "feedback_001",
  "message_id": "msg_002",
  "rating": 1,
  "comment": "Incorrect answer",
  "created_at": "2026-06-08T15:01:00Z"
}
```

## Fields

| Field | Type |
|-------|------|
| _id  | ObjectId |
| message_id | ObjectId |
| rating | int |
| comment | string |
| created_at | datetime |

---

# Qdrant Collection

Collection name:

```text
learning_assistant
```

Vector configuration:

```text
Dimension: 768
Distance: Cosine
```

## Point Structure

| Component | Type | Description |
|-----------|------|-------------|
| id | UUID/Uint | Ánh xạ trực tiếp từ `chunk_id` |
| vector | list[float] | Mảng vector sinh ra từ Embedding Model |
| payload | object | JSON chứa siêu dữ liệu (định nghĩa bên dưới) |

---

# Chunk Payload

## Example

```json
{
  "dataset_id": "dataset_001", // tạm thời để none 
  "document_id": "doc_001",
  "chunk_id": "123e4567-e89b-12d3-a456-426614174000",
  "chunk_index": 1, 
  "chunk_text": "Gradient descent is...",
  "source": "lecture_1.pdf",
  "version": 1,
  "embedding_model": "gemini-embedding-001"
}
```

## Fields

| Field | Type | Description |
|---------|---------|---------|
| dataset_id | string | Dataset reference |
| document_id | string | Document reference |
| chunk_id | UUID | Chunk identifier |
| chunk_index | int | Chunk index |
| chunk_text | string | Original chunk |
| source | string | File name |
| version | int | Document version |
| embedding_model | string | Embedding model's name |

---

# Role:
- user
- assistant
- system

# Relationships

```text
Dataset (1)
 └── Documents (N)
      
Documents (1)
  └── Chunks payload (Qdrant) (N)

Conversation (1)
 └── Messages (N)
     
Messages (1)
      └── Feedback (1)
```