from pathlib import Path
from typing import List, Dict, Any
from unstructured.partition.auto import partition
from app.models.parse_element import ParsedElement


class ParsingService:
    def __init__(self, strategy: str = "fast", languages: List[str] = None):
        """
        strategy: "fast" | "hi_res" | "ocr_only" (dùng "hi_res" nếu cần OCR cho PDF scan)
        languages: list mã ngôn ngữ cho OCR, ví dụ ["vie", "eng"]
        """
        self.strategy = strategy
        self.languages = languages or ["eng"]

    def parse(self, file_path: str) -> List[ParsedElement]:
        """
        Parse file (pdf, docx, txt, md) -> list các dict gồm text + metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")

        elements = partition(
            filename=str(path),
            strategy=self.strategy,
            languages=self.languages,
        )

        results = []
        for el in elements:
            text = str(el).strip()
            if not text:
                continue
            to_append = ParsedElement(
                text= text,
                page_number= getattr(el.metadata, "page_number", None),
                source= path.name
            )
            results.append(to_append)
        
        return results
