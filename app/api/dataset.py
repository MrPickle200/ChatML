from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil
import uuid
import os

UPLOAD_DIR = Path("data") / "dataset"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/dataset")

@router.post("/")
async def upload_dataset(file : UploadFile = File(...)):
    dataset_id = str(uuid.uuid4())
    dataset_dir = UPLOAD_DIR / dataset_id
    pth_to_save = dataset_dir / file.filename
    dataset_dir.mkdir(exist_ok= True, parents= True)

    with pth_to_save.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "status" : "ok",
        "dataset_id" : dataset_id, 
        "message" : f"Save to {pth_to_save}"
    }

@router.get("/")
async def list_dataset():
    list_name = os.listdir(UPLOAD_DIR)
    return {
        "status" : "ok",
        "list_dataset" : list_name
    }

@router.get("/{dataset_id}")
async def get_dataset():
    return {
        "status" : "ok"
    }

@router.delete("/{dataset_id}")
async def delete_dataset():
    return {
        "status" : "ok"
    }