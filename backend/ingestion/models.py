from pydantic import BaseModel
from typing import List

class FileInfo(BaseModel):
    path: str
    language: str | None
    size: int

class RepositoryMetadata(BaseModel):
    url: str
    name: str
    total_files: int
    languages_detected: List[str]
    files: List[FileInfo]
