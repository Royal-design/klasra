import hashlib
import io
import os
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import AppError

# Allow-listed educational file types with canonical MIME types.
# TODO(security): Integrate antivirus/malware scanning API and CDR content stripping
# (for PDF/Office macros) before production launch.
ALLOWED_FILE_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain; charset=utf-8",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

ZIP_BASED_EXTS = {".docx", ".pptx"}
SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ -]")


@dataclass(frozen=True)
class SavedUpload:
    original_filename: str
    storage_key: str
    content_type: str
    size_bytes: int
    sha256_checksum: str


def sanitize_display_filename(raw_filename: str) -> str:
    """Strip directory traversal and unsafe header characters for display only."""
    base = Path(raw_filename or "file").name
    cleaned = SAFE_FILENAME_CHARS.sub("_", base).strip()
    return (cleaned or "attachment")[:255]


def _validate_magic_bytes(ext: str, content: bytes) -> None:
    if ext == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise AppError(415, "INVALID_FILE_CONTENT", "File content is not a valid PDF.")
    elif ext == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise AppError(415, "INVALID_FILE_CONTENT", "File content is not a valid PNG.")
    elif ext in {".jpg", ".jpeg"}:
        if not content.startswith(b"\xff\xd8\xff"):
            raise AppError(415, "INVALID_FILE_CONTENT", "File content is not a valid JPEG.")
    elif ext == ".txt":
        if b"\x00" in content:
            raise AppError(415, "INVALID_FILE_CONTENT", "Binary content is not allowed in .txt files.")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AppError(415, "INVALID_FILE_CONTENT", "Text files must be UTF-8 encoded.") from exc
    elif ext in ZIP_BASED_EXTS:
        if not content.startswith(b"PK\x03\x04"):
            raise AppError(415, "INVALID_FILE_CONTENT", f"File content is not a valid {ext} archive.")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for member in zf.namelist():
                    # Prevent Zip Slip / path traversal entries inside Office ZIP containers
                    normalized = member.replace("\\", "/")
                    if normalized.startswith("/") or ".." in normalized.split("/"):
                        raise AppError(
                            415,
                            "UNSAFE_ARCHIVE_PATH",
                            "Uploaded archive contains unsafe path entries.",
                        )
        except zipfile.BadZipFile as exc:
            raise AppError(415, "INVALID_FILE_CONTENT", f"Corrupted {ext} archive.") from exc


def save_uploaded_file(
    *,
    storage_dir: str,
    raw_filename: str,
    content: bytes,
    max_bytes: int,
) -> SavedUpload:
    if len(content) == 0:
        raise AppError(400, "EMPTY_FILE", "Uploaded file cannot be empty.")
    if len(content) > max_bytes:
        raise AppError(
            413,
            "FILE_TOO_LARGE",
            f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)} MB.",
        )

    display_name = sanitize_display_filename(raw_filename)
    ext = Path(display_name).suffix.lower()
    if ext not in ALLOWED_FILE_TYPES:
        raise AppError(
            415,
            "UNSUPPORTED_FILE_TYPE",
            f"Unsupported file type. Allowed types: {', '.join(sorted(ALLOWED_FILE_TYPES))}.",
        )

    _validate_magic_bytes(ext, content)

    base_dir = Path(storage_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid.uuid4().hex}{ext}"
    target_path = (base_dir / storage_key).resolve()
    if not str(target_path).startswith(str(base_dir) + os.sep):
        raise AppError(400, "INVALID_STORAGE_PATH", "Resolved storage path is invalid.")

    target_path.write_bytes(content)

    return SavedUpload(
        original_filename=display_name,
        storage_key=storage_key,
        content_type=ALLOWED_FILE_TYPES[ext],
        size_bytes=len(content),
        sha256_checksum=hashlib.sha256(content).hexdigest(),
    )


def resolve_stored_file_path(*, storage_dir: str, storage_key: str) -> Path:
    base_dir = Path(storage_dir).resolve()
    # Only allow a flat UUID filename — never allow directory separators in storage_key.
    safe_key = Path(storage_key).name
    if safe_key != storage_key:
        raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.")
    target_path = (base_dir / safe_key).resolve()
    if not str(target_path).startswith(str(base_dir) + os.sep) or not target_path.is_file():
        raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.")
    return target_path
