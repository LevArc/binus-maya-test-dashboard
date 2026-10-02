"""Loopback-only dashboard API. Start with uvicorn bound to 127.0.0.1."""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from .service import RunManager

STATIC = Path(__file__).resolve().parents[1] / "static"


def create_app(manager=None):
    manager = manager or RunManager()
    app = FastAPI(title="Maya test console", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def reject_foreign_hosts(request: Request, call_next):
        if request.url.hostname not in ("127.0.0.1", "localhost", "testserver"):
            return JSONResponse({"detail": "Only local hosts are allowed"}, status_code=403)
        return await call_next(request)

    @app.get("/")
    def homepage():
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/static/{name}")
    def static_file(name: str):
        if name not in ("style.css", "app.js"):
            raise HTTPException(404)
        return FileResponse(STATIC / name, headers={"Cache-Control": "no-store"})

    @app.post("/api/runs", status_code=202)
    def start(request: Request):
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            raise HTTPException(403, "Cross-origin runs are not allowed")
        try:
            return {"id": manager.start()}
        except RuntimeError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/runs")
    def runs():
        return manager.list_runs()

    @app.get("/api/runs/{run_id}")
    def run(run_id: str):
        record = manager.get(run_id)
        if not record:
            raise HTTPException(404)
        return record

    @app.get("/api/runs/{run_id}/evidence/{filename}")
    def evidence(run_id: str, filename: str):
        record = manager.get(run_id)
        if not record or filename not in ("schedule.png", "materials.png") or not any(
            step.get("screenshot") == filename for step in record["steps"]
        ):
            raise HTTPException(404)
        path = manager.root / run_id / filename
        if not path.is_file():
            raise HTTPException(404)
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @app.get("/api/events")
    async def events(request: Request):
        async def stream():
            version = -1
            while not await request.is_disconnected():
                version, records = await asyncio.to_thread(manager.changes, version, 15)
                yield f"data: {json.dumps(records)}\n\n"
        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})

    return app


app = create_app()
