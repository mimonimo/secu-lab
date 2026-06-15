"""실습 모듈 로더.

각 모듈은 modules/<id>/ 폴더 하나로 구성된다:
    module.yaml      : 메타데이터 (필수)
    guide.md         : 학생용/강사용 진행 가이드 (선택)
    docker-compose.yml : Docker 런타임 정의 (runtime.type == docker-compose 일 때)

module.yaml 스키마 예:
    id: "01-web-juiceshop"
    title: "웹 해킹 입문 - OWASP Juice Shop"
    category: "웹 보안"
    session: 4
    difficulty: "입문"
    duration: "60분"
    summary: "한 줄 요약"
    objectives: ["학습목표1", "학습목표2"]
    multi_user: true
    runtime:
      type: "docker-compose"   # docker-compose | manual | none
      compose_file: "docker-compose.yml"
      url: "http://localhost:3000"
      lan_port: 3000
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import CURRICULUM_FILE, MODULES_DIR


@dataclass
class Runtime:
    type: str = "none"  # docker-compose | manual | none
    compose_file: str | None = None
    url: str | None = None
    lan_port: int | None = None
    notes: str | None = None


@dataclass
class Module:
    id: str
    title: str
    path: Path
    category: str = "기타"
    session: int | None = None
    difficulty: str = "입문"
    duration: str = ""
    summary: str = ""
    objectives: list[str] = field(default_factory=list)
    multi_user: bool = False
    runtime: Runtime = field(default_factory=Runtime)
    guide_md: str | None = None

    @property
    def compose_path(self) -> Path | None:
        if self.runtime.type == "docker-compose" and self.runtime.compose_file:
            return self.path / self.runtime.compose_file
        return None


def _parse_runtime(raw: dict[str, Any] | None) -> Runtime:
    raw = raw or {}
    return Runtime(
        type=raw.get("type", "none"),
        compose_file=raw.get("compose_file"),
        url=raw.get("url"),
        lan_port=raw.get("lan_port"),
        notes=raw.get("notes"),
    )


def _load_one(module_dir: Path) -> Module | None:
    meta_file = module_dir / "module.yaml"
    if not meta_file.exists():
        return None
    data = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}

    guide_file = module_dir / "guide.md"
    guide_md = guide_file.read_text(encoding="utf-8") if guide_file.exists() else None

    return Module(
        id=data.get("id", module_dir.name),
        title=data.get("title", module_dir.name),
        path=module_dir,
        category=data.get("category", "기타"),
        session=data.get("session"),
        difficulty=data.get("difficulty", "입문"),
        duration=data.get("duration", ""),
        summary=data.get("summary", ""),
        objectives=data.get("objectives", []) or [],
        multi_user=bool(data.get("multi_user", False)),
        runtime=_parse_runtime(data.get("runtime")),
        guide_md=guide_md,
    )


def load_modules() -> list[Module]:
    """modules/ 디렉토리에서 모든 모듈을 로드한다. 매 요청마다 새로 읽어 핫리로드를 지원."""
    if not MODULES_DIR.exists():
        return []
    mods: list[Module] = []
    for child in sorted(MODULES_DIR.iterdir()):
        if child.is_dir():
            m = _load_one(child)
            if m:
                mods.append(m)
    return mods


def get_module(module_id: str) -> Module | None:
    for m in load_modules():
        if m.id == module_id:
            return m
    return None


def load_curriculum() -> dict[int, dict[str, str]]:
    """curriculum.yaml 에서 회차별 메타(title, goal)를 로드. 없으면 빈 dict."""
    if not CURRICULUM_FILE.exists():
        return {}
    data = yaml.safe_load(CURRICULUM_FILE.read_text(encoding="utf-8")) or {}
    out: dict[int, dict[str, str]] = {}
    for item in data.get("sessions", []) or []:
        s = item.get("session")
        if s is None:
            continue
        out[int(s)] = {
            "title": item.get("title", ""),
            "goal": item.get("goal", ""),
        }
    return out
