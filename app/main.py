from fastapi import FastAPI
from app.api.dataset import router as dataset_router

app = FastAPI()
app.include_router(dataset_router)

@app.get("/")
def health():
    return {"status" : "hello"}