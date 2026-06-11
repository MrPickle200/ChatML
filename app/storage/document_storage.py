from pathlib import Path
import aiofiles
import shutil


class LocalStorage:

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file, document_id: str) -> Path:
        document_dir = self.base_dir / document_id
        document_dir.mkdir(parents=True, exist_ok=True)
        pth_to_save = document_dir / file.filename

        async with aiofiles.open(pth_to_save, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                await buffer.write(chunk)

        return pth_to_save

    async def replace(self, file, old_path: Path) -> Path:
        pth_to_save = old_path.parent / file.filename

        if old_path.exists() and old_path != pth_to_save:
            old_path.unlink()

        async with aiofiles.open(pth_to_save, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                await buffer.write(chunk)

        return pth_to_save

    def delete(self, document_id: str):
        pth = self.base_dir / document_id
        if not pth.exists():
            raise FileNotFoundError(f"Directory not found: {pth}")
        shutil.rmtree(pth)