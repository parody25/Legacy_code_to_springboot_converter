import io
import os
import zipfile
from typing import List, Tuple

from app.config import settings


JAVA_EXTS = {".java", ".properties", ".xml"}


def _iter_files(root_dir: str) -> List[str]:
    paths: List[str] = []
    for base, _, files in os.walk(root_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in JAVA_EXTS:
                paths.append(os.path.join(base, f))
    return paths


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def extract_zip_to_workspace(uploaded_bytes: bytes, workspace_dir: str) -> str:
    os.makedirs(workspace_dir, exist_ok=True)
    project_dir = os.path.join(workspace_dir, "uploaded")
    if os.path.exists(project_dir):
        # clean
        for base, dirs, files in os.walk(project_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(base, name))
            for name in dirs:
                os.rmdir(os.path.join(base, name))
    os.makedirs(project_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(uploaded_bytes), 'r') as zf:
        zf.extractall(project_dir)
    return project_dir


def chunk_project(project_dir: str) -> List[Tuple[str, int, str]]:
    files = _iter_files(project_dir)
    chunks_meta: List[Tuple[str, int, str]] = []
    for path in files:
        content = _read_text(path)
        if not content:
            continue
        chunks = _chunk_text(content, settings.chunk_size, settings.chunk_overlap)
        for i, ch in enumerate(chunks):
            chunks_meta.append((path, i, ch))
    return chunks_meta

