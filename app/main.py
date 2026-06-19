from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.document import router as document_router
from app.api.chat import router as chat_router
from app.api.benchmark import router as benchmark_router
from app.database.mongodb import db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
app.include_router(chat_router)
app.include_router(benchmark_router)

app.mount("/web", StaticFiles(directory="web"), name="web")

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