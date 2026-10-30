import re
import uuid
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import get_settings
from app.schemas import AnalysisResult, UploadInfo
from app.services.nebius import ModelError
from app.services.pipeline import run_pipeline
from app.services.tavily import SearchError
from app.services.tokens import count_tokens

router = APIRouter(prefix="/api", tags=["logs"])
_ID = re.compile(r"^[a-f0-9]{12}$")


def _path(upload_id: str):
    if not _ID.match(upload_id):
        raise HTTPException(400, "Invalid id")
    return get_settings().uploads_dir / f"{upload_id}.log"


def _register(filename: str, raw: bytes) -> UploadInfo:
    s = get_settings()
    if len(raw) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {s.max_upload_mb} MB")
    text = raw.decode("utf-8", errors="replace")
    if not text.strip():
        raise HTTPException(400, "File is empty")
    uid = uuid.uuid4().hex[:12]
    _path(uid).write_text(text, encoding="utf-8")
    (s.uploads_dir / f"{uid}.name").write_text(filename, encoding="utf-8")
    return UploadInfo(
        upload_id=uid,
        filename=filename,
        size_bytes=len(raw),
        line_count=text.count("\n") + 1,
        token_count=count_tokens(text),
        preview="\n".join(text.splitlines()[:40]),
    )


@router.post("/upload", response_model=UploadInfo)
async def upload(file: UploadFile = File(...)):
    return _register(file.filename or "logs.txt", await file.read())


@router.get("/samples")
async def list_samples():
    d = get_settings().samples_dir
    return [p.name for p in sorted(d.glob("*.log"))] if d.exists() else []


@router.post("/samples/{name}", response_model=UploadInfo)
async def use_sample(name: str):
    p = get_settings().samples_dir / name
    if not re.match(r"^[\w.-]+\.log$", name) or not p.is_file():
        raise HTTPException(404, "Sample not found")
    return _register(name, p.read_bytes())


@router.post("/analyze/{upload_id}", response_model=AnalysisResult)
async def analyze(upload_id: str):
    p = _path(upload_id)
    if not p.is_file():
        raise HTTPException(404, "Upload not found")
    name_file = p.with_suffix(".name")
    filename = name_file.read_text() if name_file.exists() else p.name
    try:
        result = await run_pipeline(upload_id, filename, p.read_text(encoding="utf-8"))
    except (ModelError, SearchError) as e:
        raise HTTPException(502, str(e))
    (get_settings().results_dir / f"{upload_id}.json").write_text(result.model_dump_json(indent=2))
    return result


@router.get("/results/{upload_id}", response_model=AnalysisResult)
async def get_result(upload_id: str):
    if not _ID.match(upload_id):
        raise HTTPException(400, "Invalid id")
    p = get_settings().results_dir / f"{upload_id}.json"
    if not p.is_file():
        raise HTTPException(404, "Result not found")
    return AnalysisResult.model_validate_json(p.read_text())
