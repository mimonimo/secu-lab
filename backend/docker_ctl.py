"""Docker Compose 기반 실습 환경 제어.

`docker compose` (v2) CLI를 subprocess로 호출한다. Win11 / macOS / Linux 공통.
컨테이너 이름 충돌과 일괄 정리를 위해 프로젝트명에 접두사를 붙인다.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from .config import COMPOSE_PROJECT_PREFIX
from .modules import Module


@dataclass
class ActionResult:
    ok: bool
    message: str
    detail: str = ""


def _project_name(module: Module) -> str:
    # docker compose 프로젝트명은 소문자/숫자/'-' 권장
    safe = "".join(c if c.isalnum() else "-" for c in module.id).lower().strip("-")
    return f"{COMPOSE_PROJECT_PREFIX}-{safe}"


def docker_available() -> bool:
    """docker CLI 존재 + 데몬 응답 여부."""
    if shutil.which("docker") is None:
        return False
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _compose_cmd(module: Module, *args: str) -> list[str]:
    compose_path = module.compose_path
    assert compose_path is not None
    return [
        "docker",
        "compose",
        "-p",
        _project_name(module),
        "-f",
        str(compose_path),
        *args,
    ]


def _run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def start(module: Module) -> ActionResult:
    if module.runtime.type != "docker-compose" or module.compose_path is None:
        return ActionResult(False, "이 모듈은 Docker 런타임이 아닙니다.")
    if not module.compose_path.exists():
        return ActionResult(False, f"compose 파일을 찾을 수 없습니다: {module.compose_path}")
    if not docker_available():
        return ActionResult(False, "Docker를 사용할 수 없습니다. Docker Desktop이 실행 중인지 확인하세요.")
    try:
        r = _run(_compose_cmd(module, "up", "-d"))
    except subprocess.TimeoutExpired:
        return ActionResult(False, "실행 시간 초과 (이미지 다운로드가 오래 걸릴 수 있습니다).")
    if r.returncode == 0:
        return ActionResult(True, "실습 환경을 시작했습니다.", r.stderr or r.stdout)
    return ActionResult(False, "시작 실패", r.stderr or r.stdout)


def stop(module: Module) -> ActionResult:
    if module.runtime.type != "docker-compose" or module.compose_path is None:
        return ActionResult(False, "이 모듈은 Docker 런타임이 아닙니다.")
    if not docker_available():
        return ActionResult(False, "Docker를 사용할 수 없습니다.")
    try:
        r = _run(_compose_cmd(module, "down"))
    except subprocess.TimeoutExpired:
        return ActionResult(False, "종료 시간 초과.")
    if r.returncode == 0:
        return ActionResult(True, "실습 환경을 종료했습니다.", r.stderr or r.stdout)
    return ActionResult(False, "종료 실패", r.stderr or r.stdout)


def status(module: Module) -> str:
    """모듈 상태: running | stopped | unavailable | n/a"""
    if module.runtime.type != "docker-compose" or module.compose_path is None:
        return "n/a"
    if not docker_available():
        return "unavailable"
    if not module.compose_path.exists():
        return "unavailable"
    try:
        r = _run(_compose_cmd(module, "ps", "-q"), timeout=20)
    except subprocess.TimeoutExpired:
        return "unavailable"
    if r.returncode != 0:
        return "unavailable"
    # 실행 중인 컨테이너 ID가 하나라도 있으면 running
    return "running" if r.stdout.strip() else "stopped"
