"""경로 및 전역 설정."""
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
MODULES_DIR = ROOT_DIR / "modules"
CURRICULUM_FILE = ROOT_DIR / "curriculum.yaml"
FRONTEND_DIR = ROOT_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"

# Docker Compose 프로젝트 접두사 (컨테이너 이름 충돌 방지 + 일괄 정리 용이)
COMPOSE_PROJECT_PREFIX = "seculab"
