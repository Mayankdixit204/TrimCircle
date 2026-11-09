import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


RUNTIME_DIR = Path(__file__).resolve().parent.parent / "runtime"
JOB_DIR = RUNTIME_DIR / "jobs"
DATABASE_PATH = RUNTIME_DIR / "trimcircle.db"
DEFAULT_RETENTION_HOURS = 24


def _now() -> datetime:
    return datetime.now(timezone.utc)


def initialize() -> None:
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tryon_jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                style_id TEXT NOT NULL,
                style_name TEXT NOT NULL,
                color TEXT NOT NULL,
                texture TEXT NOT NULL,
                input_path TEXT NOT NULL,
                result_path TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def create_job(style: dict, color: str, texture: str, input_bytes: bytes) -> dict:
    initialize()
    job_id = str(uuid.uuid4())
    job_directory = JOB_DIR / job_id
    job_directory.mkdir(parents=True, exist_ok=False)
    input_path = job_directory / "input.png"
    input_path.write_bytes(input_bytes)
    created = _now()
    expires = created + timedelta(hours=DEFAULT_RETENTION_HOURS)
    values = (
        job_id, "awaiting_gpu", 10, style["id"], style["name"], color, texture,
        str(input_path), None, None, created.isoformat(), created.isoformat(), expires.isoformat(),
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """INSERT INTO tryon_jobs
            (id,status,progress,style_id,style_name,color,texture,input_path,result_path,error,created_at,updated_at,expires_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            values,
        )
        connection.commit()
    return get_job(job_id)


def get_job(job_id: str) -> dict | None:
    initialize()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM tryon_jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def update_job(job_id: str, **changes) -> dict | None:
    allowed = {"status", "progress", "result_path", "error"}
    selected = {key: value for key, value in changes.items() if key in allowed}
    if not selected:
        return get_job(job_id)
    selected["updated_at"] = _now().isoformat()
    assignments = ", ".join(f"{key} = ?" for key in selected)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            f"UPDATE tryon_jobs SET {assignments} WHERE id = ?",
            (*selected.values(), job_id),
        )
        connection.commit()
    return get_job(job_id)


def public_job(job: dict) -> dict:
    return {
        "id": job["id"],
        "status": job["status"],
        "progress": job["progress"],
        "style": {"id": job["style_id"], "name": job["style_name"]},
        "color": job["color"],
        "texture": job["texture"],
        "error": job["error"],
        "created_at": job["created_at"],
        "expires_at": job["expires_at"],
        "result_ready": bool(job["result_path"]),
    }


def delete_job(job_id: str) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job_directory = JOB_DIR / job_id
    if job_directory.resolve().parent == JOB_DIR.resolve() and job_directory.exists():
        for path in job_directory.iterdir():
            if path.is_file():
                path.unlink()
        job_directory.rmdir()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DELETE FROM tryon_jobs WHERE id = ?", (job_id,))
        connection.commit()
    return True


def cleanup_expired() -> int:
    initialize()
    now = _now().isoformat()
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute("SELECT id FROM tryon_jobs WHERE expires_at < ?", (now,)).fetchall()
    for (job_id,) in rows:
        delete_job(job_id)
    return len(rows)
