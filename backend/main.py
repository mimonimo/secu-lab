"""FastAPI 애플리케이션 - 대시보드 + 모듈 제어 API."""
from __future__ import annotations

import socket

import markdown as md
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import docker_ctl
from .config import STATIC_DIR, TEMPLATES_DIR
from .modules import get_module, load_curriculum, load_modules

app = FastAPI(title="secu-lab", description="보안 실습 관제 플랫폼")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _lan_ip() -> str:
    """이 PC의 LAN IP를 추정 (학생 접속 주소 안내용)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 실제 전송 없음, 라우팅 인터페이스 확인용
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _lan_url(url: str | None) -> str | None:
    """localhost URL을 LAN IP로 치환 (학생 접속용 주소)."""
    if not url:
        return None
    ip = _lan_ip()
    return url.replace("localhost", ip).replace("127.0.0.1", ip)


# ----------------------------- 페이지 -----------------------------
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    modules = load_modules()
    docker_ok = docker_ctl.docker_available()
    curriculum = load_curriculum()

    # 회차(session)별 그룹화 + 커리큘럼 제목/목표 결합.
    by_session: dict[object, list] = {}
    for m in modules:
        key = m.session if m.session is not None else None
        by_session.setdefault(key, []).append(m)

    def _sort_key(k: object) -> tuple[int, float]:
        # None(회차 미지정)은 맨 뒤로
        return (1, 0.0) if k is None else (0, float(k))  # type: ignore[arg-type]

    sessions = []
    for key in sorted(by_session.keys(), key=_sort_key):
        meta = curriculum.get(key, {}) if key is not None else {}
        sessions.append(
            {
                "session": key,
                "label": f"{key}회차" if key is not None else "회차 미지정",
                "title": meta.get("title", ""),
                "goal": meta.get("goal", ""),
                "modules": by_session[key],
            }
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sessions": sessions,
            "total": len(modules),
            "docker_ok": docker_ok,
            "lan_ip": _lan_ip(),
        },
    )


@app.get("/module/{module_id}", response_class=HTMLResponse)
def module_detail(request: Request, module_id: str) -> HTMLResponse:
    module = get_module(module_id)
    if module is None:
        return HTMLResponse("<h1>모듈을 찾을 수 없습니다.</h1>", status_code=404)

    guide_html = None
    if module.guide_md:
        guide_html = md.markdown(
            module.guide_md,
            extensions=["fenced_code", "tables", "toc", "sane_lists"],
        )

    return templates.TemplateResponse(
        "module.html",
        {
            "request": request,
            "m": module,
            "guide_html": guide_html,
            "lan_url": _lan_url(module.runtime.url),
            "docker_ok": docker_ctl.docker_available(),
        },
    )


# ----------------------------- API -----------------------------
@app.get("/api/modules")
def api_modules() -> JSONResponse:
    out = []
    for m in load_modules():
        out.append(
            {
                "id": m.id,
                "title": m.title,
                "category": m.category,
                "session": m.session,
                "runtime_type": m.runtime.type,
                "status": docker_ctl.status(m),
            }
        )
    return JSONResponse(out)


@app.get("/api/module/{module_id}/status")
def api_status(module_id: str) -> JSONResponse:
    module = get_module(module_id)
    if module is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(
        {
            "id": module.id,
            "status": docker_ctl.status(module),
            "url": module.runtime.url,
            "lan_url": _lan_url(module.runtime.url),
        }
    )


@app.post("/api/module/{module_id}/start")
def api_start(module_id: str) -> JSONResponse:
    module = get_module(module_id)
    if module is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    res = docker_ctl.start(module)
    return JSONResponse(
        {"ok": res.ok, "message": res.message, "detail": res.detail},
        status_code=200 if res.ok else 400,
    )


@app.post("/api/module/{module_id}/stop")
def api_stop(module_id: str) -> JSONResponse:
    module = get_module(module_id)
    if module is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    res = docker_ctl.stop(module)
    return JSONResponse(
        {"ok": res.ok, "message": res.message, "detail": res.detail},
        status_code=200 if res.ok else 400,
    )


@app.get("/api/health")
def api_health() -> JSONResponse:
    return JSONResponse({"status": "ok", "docker": docker_ctl.docker_available()})
