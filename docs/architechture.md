# Overall

                ┌─────────────┐
                │    User     │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │   FastAPI   │
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
 ┌───────────┐  ┌───────────┐  ┌───────────┐
 │ MongoDB   │  │  Qdrant   │  │    LLM    │
 └───────────┘  └───────────┘  └───────────┘
                       ▲              ▲
                       │              │
                       └──────┬───────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ Embeddings  │
                       └─────────────┘



# Ingestion

       Upload File
           ↓
         Parse
           ↓
         Chunk
           ↓
         Embed
           ↓
     Store in Qdrant


# Chat flow

        Question
           ↓
         Embed
           ↓
        Retrieve
           ↓
       Build Context
           ↓
          LLM
           ↓
        Answer


