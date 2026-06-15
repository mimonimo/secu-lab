# 🛡️ secu-lab — 보안 실습 관제 플랫폼

고등학생 진로·직업 체험용 **정보보안 실습**을 한곳에서 켜고 끄고 진행할 수 있는 로컬 대시보드입니다.
강사(여러분)가 메인으로 시연하면서, 같은 와이파이의 학생들도 각자 노트북으로 핸즈온할 수 있습니다.

> ⚠️ **사용 원칙**
> - 모든 실습은 **로컬 / LAN 격리 환경**에서만 동작합니다.
> - 실제 외부 서비스나 타인의 정보를 대상으로 하지 않습니다.
> - 인터넷(공인 IP)에 절대 노출하지 마세요.
> - 교육 목적 전용입니다.

---

## 1. 구성

```
secu-lab/
├─ run.py                  # 실행 진입점
├─ requirements.txt
├─ backend/                # FastAPI 대시보드 + Docker 제어
│   ├─ main.py             # 라우트
│   ├─ modules.py          # 모듈 로더 (modules/ 폴더 스캔)
│   ├─ docker_ctl.py       # docker compose 제어
│   └─ config.py
├─ frontend/               # 대시보드 UI (Tailwind CDN)
│   ├─ templates/          # index.html, module.html
│   └─ static/             # app.js, style.css
└─ modules/                # ★ 실습 모듈들 (폴더 1개 = 실습 1개)
    ├─ 01-web-juiceshop/        # 웹 해킹 입문 (OWASP Juice Shop)
    └─ 02-phishing-awareness/   # 피싱 인식 실습 (자기완결형 Flask)
```

## 2. 준비물 (Win11 기준)

1. **Python 3.10+** — [python.org](https://www.python.org/) 또는 Microsoft Store
2. **Docker Desktop** — 실습 환경 실행용. 설치 후 실행해 두세요.
3. (선택) **VMware** — 랜섬웨어 등 위험 실습을 격리 VM에서 돌릴 때.

## 3. 설치 & 실행

```powershell
# secu-lab 폴더에서
python -m venv .venv
.\.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 강사 PC 전용 (localhost)
python run.py

# 학생도 같은 와이파이에서 접속하게 하려면
python run.py --lan
```

- 브라우저에서 `http://127.0.0.1:8800` 접속 → 대시보드.
- `--lan` 모드면 콘솔에 표시되는 **이 PC의 LAN IP**(예: `http://192.168.0.x:8800`)를 학생에게 공유.

## 4. 사용법

1. 대시보드에서 회차별 실습 카드를 확인합니다.
2. 카드 또는 상세 페이지의 **[▶ 시작]** 으로 실습 환경(컨테이너)을 켭니다.
   - 최초 실행은 이미지 다운로드로 시간이 걸릴 수 있습니다.
3. 표시되는 접속 주소로 강사/학생이 실습합니다.
4. 끝나면 **[■ 종료]** 로 정리합니다. (상태는 10초마다 자동 갱신)

## 5. 새 실습 모듈 추가하기

`modules/` 안에 폴더를 하나 만들고 `module.yaml`을 넣으면 끝입니다.

```yaml
id: "03-my-lab"
title: "내 실습"
category: "웹 보안"
session: 6
difficulty: "입문"
duration: "45분"
summary: "한 줄 설명"
objectives: ["학습목표1", "학습목표2"]
multi_user: true
runtime:
  type: "docker-compose"     # docker-compose | manual | none
  compose_file: "docker-compose.yml"
  url: "http://localhost:8080"
  lan_port: 8080
```

- `guide.md`(선택)를 같이 넣으면 상세 페이지에 가이드가 렌더링됩니다.
- `runtime.type: docker-compose`면 같은 폴더의 `docker-compose.yml`을 대시보드가 제어합니다.
- Docker가 아닌 실습(예: VMware VM)은 `type: manual`로 두고 `runtime.notes`에 실행 안내를 적으세요.

## 6. 기본 제공 모듈

| 모듈 | 내용 | 런타임 |
|---|---|---|
| `01-web-juiceshop` | OWASP Juice Shop으로 SQL 인젝션·XSS 체험 | Docker (포트 3000) |
| `02-phishing-awareness` | 가상 브랜드 가짜 로그인 → 즉시 폭로 + 식별법 | Docker (포트 5001) |

## 7. API (참고)

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/` | 대시보드 |
| GET | `/module/{id}` | 모듈 상세 + 가이드 |
| GET | `/api/modules` | 전체 모듈 목록(JSON) |
| GET | `/api/module/{id}/status` | 상태 조회 |
| POST | `/api/module/{id}/start` | 실습 시작 |
| POST | `/api/module/{id}/stop` | 실습 종료 |
| GET | `/api/health` | 헬스체크 + Docker 가용 여부 |

## 8. 안전 / 윤리 안내 (학생 교육용)

- 이 실습들은 **방어를 이해하기 위해 공격을 체험**하는 것입니다.
- 배운 기술을 **허락 없이 실제 사람/서비스에 사용하면 법(정보통신망법 등) 위반**입니다.
- 항상 **본인 소유** 또는 **명시적 허가를 받은** 환경에서만 테스트하세요.
