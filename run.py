#!/usr/bin/env python3
"""
secu-lab 실행 진입점.

사용법:
    python run.py                # 제어판: localhost 전용 (강사 PC에서만)
    python run.py --lan          # 같은 와이파이의 학생도 대시보드 접속 허용
    python run.py --port 9000    # 포트 변경

주의:
- 이 도구는 '같은 로컬 네트워크(LAN)' 안에서의 보안 교육 실습용입니다.
- 인터넷(공인 IP)에 절대 노출하지 마세요. 모든 실습 환경은 격리된 환경에서 실행됩니다.
"""
import argparse
import sys
from pathlib import Path

import uvicorn

BASE_DIR = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="secu-lab 보안 실습 관제 플랫폼")
    parser.add_argument(
        "--lan",
        action="store_true",
        help="같은 LAN의 다른 기기(학생 노트북)에서도 대시보드에 접속 허용 (0.0.0.0 바인딩)",
    )
    parser.add_argument("--port", type=int, default=8800, help="대시보드 포트 (기본 8800)")
    parser.add_argument("--reload", action="store_true", help="개발용 자동 리로드")
    args = parser.parse_args()

    host = "0.0.0.0" if args.lan else "127.0.0.1"

    # backend 패키지를 import 가능하게 경로 추가
    sys.path.insert(0, str(BASE_DIR))

    banner = f"""
================================================================
  secu-lab  |  보안 실습 관제 플랫폼
----------------------------------------------------------------
  제어판 주소 : http://{'<이 PC의 LAN IP>' if args.lan else '127.0.0.1'}:{args.port}
  바인딩      : {host}
  모드        : {'LAN 공유 (학생 접속 허용)' if args.lan else 'localhost 전용 (강사 PC)'}
----------------------------------------------------------------
  종료: Ctrl + C
================================================================
"""
    print(banner)

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
