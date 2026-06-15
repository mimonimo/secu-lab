"""
피싱 인식 실습 - 자기완결형 교육용 Flask 앱.

설계 원칙 (안전):
- 가상의 브랜드 'SkyBird'를 사용. 실제 서비스(인스타그램 등)를 사칭하지 않음.
- 입력값을 외부로 전송하지 않음. 디스크에 영구 저장하지 않음.
- 비밀번호는 폭로 화면에서 마스킹하여, 평문 자격증명을 그대로 수집/노출하지 않음.
- 로그인 시도 즉시 '이것은 피싱입니다' 폭로 화면으로 이동하여 식별법을 교육.
- 메모리에 최근 시도만 잠시 보관(강사 시연용), 컨테이너 종료 시 모두 사라짐.

이 앱은 '피싱을 알아채는 법'을 가르치기 위한 시뮬레이터이며,
실제 자격증명 탈취 도구가 아닙니다.
"""
from collections import deque
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# 강사 시연용: 최근 시도 20건만 메모리에 보관 (영구 저장 아님)
ATTEMPTS: deque = deque(maxlen=20)


def mask_password(pw: str) -> str:
    """비밀번호를 마스킹. 평문을 그대로 보관/표시하지 않는다."""
    if not pw:
        return "(빈 값)"
    if len(pw) <= 2:
        return "•" * len(pw)
    return pw[0] + "•" * (len(pw) - 2) + pw[-1]


@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    # 외부 전송/영구 저장 없음. 교육용 폭로를 위한 메타데이터만 메모리에 기록.
    ATTEMPTS.appendleft(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "username": username[:64],
            "password_masked": mask_password(password),
            "password_len": len(password),
            "ip": request.remote_addr or "?",
        }
    )

    return render_template(
        "revealed.html",
        username=username or "(입력 안 함)",
        password_masked=mask_password(password),
        password_len=len(password),
    )


@app.route("/instructor")
def instructor():
    """강사 화면: 학생들이 방금 '제출'한 정보가 공격자에게 어떻게 모이는지 보여준다."""
    return render_template("log.html", attempts=list(ATTEMPTS))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # 0.0.0.0: 같은 LAN의 학생 기기 접속 허용 (인터넷 노출 금지)
    app.run(host="0.0.0.0", port=5001)
