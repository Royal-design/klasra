import hashlib
import io
import os
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import Settings
from app.core.errors import AppError

# Allow-listed educational document/image file types with canonical MIME types.
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

# Allow-listed lesson video types (teachers on lessons only; never student submissions).
ALLOWED_VIDEO_TYPES: dict[str, str] = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}

ZIP_BASED_EXTS = {".docx", ".pptx"}
SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ -]")
STORAGE_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]+$")


@dataclass(frozen=True)
class SavedUpload:
    original_filename: str
    storage_key: str
    content_type: str
    size_bytes: int
    sha256_checksum: str


class StorageBackend(Protocol):
    supports_presigned_urls: bool

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> None: ...
    def get_bytes(self, *, storage_key: str) -> bytes: ...
    def head_object(self, *, storage_key: str) -> tuple[int, str | None]: ...
    def read_head_bytes(self, *, storage_key: str, num_bytes: int = 32) -> bytes: ...
    def generate_presigned_upload_url(
        self, *, storage_key: str, content_type: str, expires_in: int
    ) -> str: ...
    def generate_presigned_download_url(
        self,
        *,
        storage_key: str,
        filename: str,
        content_type: str,
        expires_in: int,
        inline: bool = False,
    ) -> str: ...


class LocalStorageBackend:
    """Local disk storage outside any public web root (for dev and tests)."""

    supports_presigned_urls: bool = False

    def __init__(self, storage_dir: str) -> None:
        self._base_dir = Path(storage_dir).resolve()

    def _safe_path(self, storage_key: str) -> Path:
        safe_key = Path(storage_key).name
        if safe_key != storage_key:
            raise AppError(400, "INVALID_STORAGE_PATH", "Invalid storage key.")
        target = (self._base_dir / safe_key).resolve()
        if not str(target).startswith(str(self._base_dir) + os.sep):
            raise AppError(400, "INVALID_STORAGE_PATH", "Resolved storage path is invalid.")
        return target

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._safe_path(storage_key).write_bytes(content)

    def get_bytes(self, *, storage_key: str) -> bytes:
        target = self._safe_path(storage_key)
        if not target.is_file():
            raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.")
        return target.read_bytes()

    def head_object(self, *, storage_key: str) -> tuple[int, str | None]:
        target = self._safe_path(storage_key)
        if not target.is_file():
            raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.")
        return target.stat().st_size, None

    def read_head_bytes(self, *, storage_key: str, num_bytes: int = 32) -> bytes:
        target = self._safe_path(storage_key)
        if not target.is_file():
            raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.")
        with target.open("rb") as fh:
            return fh.read(num_bytes)

    def generate_presigned_upload_url(
        self, *, storage_key: str, content_type: str, expires_in: int
    ) -> str:
        raise AppError(
            400,
            "PRESIGNED_URLS_UNSUPPORTED",
            "Direct presigned uploads require STORAGE_PROVIDER=s3. Use the multipart upload endpoint instead.",
        )

    def generate_presigned_download_url(
        self,
        *,
        storage_key: str,
        filename: str,
        content_type: str,
        expires_in: int,
        inline: bool = False,
    ) -> str:
        raise AppError(
            400,
            "PRESIGNED_URLS_UNSUPPORTED",
            "Direct presigned downloads require STORAGE_PROVIDER=s3.",
        )


class S3StorageBackend:
    """Private S3-compatible object storage (Backblaze B2, Cloudflare R2, AWS S3, Supabase)."""

    supports_presigned_urls: bool = True

    def __init__(
        self,
        *,
        endpoint_url: str | None,
        bucket: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
    ) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=storage_key,
            Body=content,
            ContentType=content_type,
        )

    def get_bytes(self, *, storage_key: str) -> bytes:
        from botocore.exceptions import ClientError

        try:
            response = self._client.get_object(Bucket=self._bucket, Key=storage_key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.") from exc
            raise AppError(503, "STORAGE_UNAVAILABLE", "File storage is temporarily unavailable.") from exc
        return response["Body"].read()

    def head_object(self, *, storage_key: str) -> tuple[int, str | None]:
        from botocore.exceptions import ClientError

        try:
            response = self._client.head_object(Bucket=self._bucket, Key=storage_key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                raise AppError(404, "FILE_NOT_FOUND", "Uploaded object not found in storage.") from exc
            raise AppError(503, "STORAGE_UNAVAILABLE", "File storage is temporarily unavailable.") from exc
        return int(response["ContentLength"]), response.get("ContentType")

    def read_head_bytes(self, *, storage_key: str, num_bytes: int = 32) -> bytes:
        from botocore.exceptions import ClientError

        end_byte = max(0, num_bytes - 1)
        try:
            response = self._client.get_object(
                Bucket=self._bucket,
                Key=storage_key,
                Range=f"bytes=0-{end_byte}",
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                raise AppError(404, "FILE_NOT_FOUND", "Uploaded object not found in storage.") from exc
            raise AppError(503, "STORAGE_UNAVAILABLE", "File storage is temporarily unavailable.") from exc
        return response["Body"].read()

    def generate_presigned_upload_url(
        self, *, storage_key: str, content_type: str, expires_in: int
    ) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": storage_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

    def generate_presigned_download_url(
        self,
        *,
        storage_key: str,
        filename: str,
        content_type: str,
        expires_in: int,
        inline: bool = False,
    ) -> str:
        disposition = "inline" if inline else "attachment"
        return self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._bucket,
                "Key": storage_key,
                "ResponseContentDisposition": f'{disposition}; filename="{filename}"',
                "ResponseContentType": content_type,
            },
            ExpiresIn=expires_in,
            HttpMethod="GET",
        )


class InMemoryStorageBackend:
    """In-memory storage double for fast, isolated automated tests."""

    supports_presigned_urls: bool = True

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> None:
        self.objects[storage_key] = content
        self.content_types[storage_key] = content_type

    def get_bytes(self, *, storage_key: str) -> bytes:
        if storage_key not in self.objects:
            raise AppError(404, "FILE_NOT_FOUND", "Stored file not found.")
        return self.objects[storage_key]

    def head_object(self, *, storage_key: str) -> tuple[int, str | None]:
        if storage_key not in self.objects:
            raise AppError(404, "FILE_NOT_FOUND", "Uploaded object not found in storage.")
        return len(self.objects[storage_key]), self.content_types.get(storage_key)

    def read_head_bytes(self, *, storage_key: str, num_bytes: int = 32) -> bytes:
        if storage_key not in self.objects:
            raise AppError(404, "FILE_NOT_FOUND", "Uploaded object not found in storage.")
        return self.objects[storage_key][:num_bytes]

    def generate_presigned_upload_url(
        self, *, storage_key: str, content_type: str, expires_in: int
    ) -> str:
        return f"https://storage.example.com/upload/{storage_key}?expires={expires_in}"

    def generate_presigned_download_url(
        self,
        *,
        storage_key: str,
        filename: str,
        content_type: str,
        expires_in: int,
        inline: bool = False,
    ) -> str:
        mode = "inline" if inline else "attachment"
        return f"https://storage.example.com/download/{storage_key}?disposition={mode}&expires={expires_in}"


def build_storage_backend(settings: Settings) -> StorageBackend:
    if settings.storage_provider == "s3":
        assert settings.s3_bucket and settings.s3_access_key_id and settings.s3_secret_access_key
        return S3StorageBackend(
            endpoint_url=settings.s3_endpoint_url,
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
        )
    return LocalStorageBackend(settings.upload_storage_dir)


def sanitize_display_filename(raw_filename: str) -> str:
    """Strip directory traversal and unsafe header characters for display only."""
    base = Path(raw_filename or "file").name
    cleaned = SAFE_FILENAME_CHARS.sub("_", base).strip()
    return (cleaned or "attachment")[:255]


def _resolve_allowed_type_and_limit(
    *,
    raw_filename: str,
    max_bytes: int,
    allow_video: bool = False,
    max_video_bytes: int | None = None,
) -> tuple[str, str, str, int]:
    """Return (display_name, ext, canonical_content_type, effective_max_bytes)."""
    display_name = sanitize_display_filename(raw_filename)
    ext = Path(display_name).suffix.lower()
    allowed = {**ALLOWED_FILE_TYPES, **ALLOWED_VIDEO_TYPES} if allow_video else ALLOWED_FILE_TYPES
    if ext not in allowed:
        raise AppError(
            415,
            "UNSUPPORTED_FILE_TYPE",
            f"Unsupported file type. Allowed types: {', '.join(sorted(allowed))}.",
        )
    if ext in ALLOWED_VIDEO_TYPES:
        effective_limit = max_video_bytes if max_video_bytes is not None else max_bytes
    else:
        effective_limit = max_bytes
    return display_name, ext, allowed[ext], effective_limit


def _format_size_limit(limit_bytes: int) -> str:
    if limit_bytes >= 1024 * 1024:
        return f"{limit_bytes // (1024 * 1024)} MB"
    return f"{limit_bytes} bytes"


def validate_magic_bytes(ext: str, content: bytes, *, header_only: bool = False) -> None:
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
        if not header_only:
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise AppError(415, "INVALID_FILE_CONTENT", "Text files must be UTF-8 encoded.") from exc
    elif ext in ZIP_BASED_EXTS:
        if not content.startswith(b"PK\x03\x04"):
            raise AppError(415, "INVALID_FILE_CONTENT", f"File content is not a valid {ext} archive.")
        if not header_only:
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    for member in zf.namelist():
                        normalized = member.replace("\\", "/")
                        if normalized.startswith("/") or ".." in normalized.split("/"):
                            raise AppError(
                                415,
                                "UNSAFE_ARCHIVE_PATH",
                                "Uploaded archive contains unsafe path entries.",
                            )
            except zipfile.BadZipFile as exc:
                raise AppError(415, "INVALID_FILE_CONTENT", f"Corrupted {ext} archive.") from exc
    elif ext == ".mp4":
        if len(content) < 12 or content[4:8] != b"ftyp":
            raise AppError(415, "INVALID_FILE_CONTENT", "File content is not a valid MP4 video.")
    elif ext == ".webm":
        if not content.startswith(b"\x1a\x45\xdf\xa3"):
            raise AppError(415, "INVALID_FILE_CONTENT", "File content is not a valid WebM video.")
    elif ext == ".mov":
        if len(content) < 12 or content[4:8] not in {b"ftyp", b"moov", b"mdat", b"wide", b"free"}:
            raise AppError(415, "INVALID_FILE_CONTENT", "File content is not a valid QuickTime MOV video.")


def prepare_presigned_upload(
    *,
    raw_filename: str,
    size_bytes: int,
    max_bytes: int,
    allow_video: bool = False,
    max_video_bytes: int | None = None,
) -> tuple[str, str, str, int]:
    """Validate filename and declared size, then return (display_name, storage_key, content_type, limit)."""
    if size_bytes <= 0:
        raise AppError(400, "EMPTY_FILE", "Uploaded file cannot be empty.")

    display_name, ext, content_type, effective_limit = _resolve_allowed_type_and_limit(
        raw_filename=raw_filename,
        max_bytes=max_bytes,
        allow_video=allow_video,
        max_video_bytes=max_video_bytes,
    )
    if size_bytes > effective_limit:
        raise AppError(
            413,
            "FILE_TOO_LARGE",
            f"File exceeds the maximum allowed size of {_format_size_limit(effective_limit)}.",
        )
    storage_key = f"{uuid.uuid4().hex}{ext}"
    return display_name, storage_key, content_type, effective_limit


def save_uploaded_file(
    *,
    storage_backend: StorageBackend,
    raw_filename: str,
    content: bytes,
    max_bytes: int,
    allow_video: bool = False,
    max_video_bytes: int | None = None,
) -> SavedUpload:
    if len(content) == 0:
        raise AppError(400, "EMPTY_FILE", "Uploaded file cannot be empty.")

    display_name, ext, content_type, effective_limit = _resolve_allowed_type_and_limit(
        raw_filename=raw_filename,
        max_bytes=max_bytes,
        allow_video=allow_video,
        max_video_bytes=max_video_bytes,
    )
    if len(content) > effective_limit:
        raise AppError(
            413,
            "FILE_TOO_LARGE",
            f"File exceeds the maximum allowed size of {_format_size_limit(effective_limit)}.",
        )

    validate_magic_bytes(ext, content, header_only=False)

    storage_key = f"{uuid.uuid4().hex}{ext}"
    storage_backend.put_bytes(
        storage_key=storage_key,
        content=content,
        content_type=content_type,
    )

    return SavedUpload(
        original_filename=display_name,
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=len(content),
        sha256_checksum=hashlib.sha256(content).hexdigest(),
    )
