from fastapi import APIRouter, UploadFile, File, HTTPException
from app.database.mongodb import document_collection
from pathlib import Path
from datetime import datetime, timezone
import aiofiles
import shutil
import uuid

UPLOAD_DIR = Path("data") / "test"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_FILE_TYPES = {"pdf", "docx", "txt", "md"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

router = APIRouter(prefix="/document")

async def validate_document(file : UploadFile):
    file_type = file.filename.split(".")[-1].lower()
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail= f"File type {file_type} not allowed. Allowed: {ALLOWED_FILE_TYPES}"    
        )
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code= 400,
            detail= f"File too big. Max size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"
        )
    await file.seek(0) # Di chuyển con trỏ về đầu file, tránh trả về file rỗng

@router.post("/upload-document")
async def upload_document(file : UploadFile = File(...)):
    await validate_document(file)

    document_id = str(uuid.uuid4())
    document_dir = UPLOAD_DIR / document_id
    pth_to_save = document_dir / file.filename
    document_dir.mkdir(exist_ok= True, parents= True)

    async with aiofiles.open(pth_to_save, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # đọc theo chunk nếu file lớn, 1MB mỗi lần 
            await buffer.write(chunk)

    metadata = {
        "_id" : document_id,
        "dataset_id" : None,
        "filename" : file.filename,
        "file_type" : file.filename.split(".")[-1].lower(),
        "file_size_byte" : pth_to_save.stat().st_size,
        "version" : 1,
        "status" : "uploaded",
        "created_at" : datetime.now(timezone.utc),
        "updated_at" : datetime.now(timezone.utc),
        "storage" : {
            "provider" : "local",
            "uri" : str(pth_to_save)
        }
    }

    try:
        await document_collection.insert_one(metadata)
        return {
            "status" : "ok",
            "document_id" : document_id, 
            "message" : "Save metadata to MongoDB"
        }
    except Exception as e:
        shutil.rmtree(document_dir)
        raise e
    

@router.post("/update-document/{document_id}")
async def update_document(document_id : str, file : UploadFile = File(...)):
    await validate_document(file)

    to_update = await document_collection.find_one({"_id" : document_id})
    if not to_update:
        raise HTTPException(status_code=404, detail = "Document not found")
    old_path = Path(to_update["storage"]["uri"])
    pth_to_save = old_path.parent / file.filename
    
    if old_path.exists() and old_path != pth_to_save:
        old_path.unlink()

    async with aiofiles.open(pth_to_save, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # đọc theo chunk nếu file lớn, 1MB mỗi lần
            await buffer.write(chunk)

    update_metadata = {
        "filename" : file.filename,
        "file_type" : file.filename.split(".")[-1].lower(),
        "file_size_byte" : pth_to_save.stat().st_size,
        "version" : to_update["version"] + 1,
        "status" : "updated",
        "updated_at" : datetime.now(timezone.utc),
        "storage" : {
            "provider" : "local",
            "uri" : str(pth_to_save)
        }
    }
    try:
        await document_collection.update_one({"_id" : document_id}, {"$set" : update_metadata})
        return {
            "status" : "ok",
            "document_id" : document_id, 
            "message" : "Updated document metadata"
        }
    except Exception as e:
        shutil.rmtree(pth_to_save)
        raise e
    
document_collection.fin

@router.get("/get-list-document")
async def list_document():
    cursor = document_collection.find({}, {"_id" : 1, "filename" : 1, "status" : 1, "version" : 1})
    list_docs = await cursor.to_list(length= None)
    return {
        "status" : "ok",
        "list_document" : list_docs
    }

@router.get("/get-document/{document_id}")
async def get_by_id(document_id : str):
    document_metadata = await document_collection.find_one({"_id" : document_id}) 
    if not document_metadata:
        raise HTTPException(status_code=404, detail= "Document not found")
    return {
        "status" : "ok",
        "metadata" : document_metadata
    }
    

@router.delete("/delete-document/{document_id}")
async def delete_by_id(document_id : str):
    pth = UPLOAD_DIR / document_id
    if not pth.exists():
        raise HTTPException(status_code=404, detail= "Document not found")
    await document_collection.delete_one({"_id" : document_id})
    shutil.rmtree(pth)
    return {
        "status" : "ok"
    }
