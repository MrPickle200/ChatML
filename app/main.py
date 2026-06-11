from fastapi import FastAPI
from app.api.document import router as document_router
from app.database.mongodb import db

app = FastAPI()
app.include_router(document_router)

@app.get("/")
def health_check():
    return {"status" : "healthy"}

@app.get("/test-db")
async def test_db():
    collections = await db.list_collection_names()
    return {
        "status" : "ok",
        "collections" : collections
    }