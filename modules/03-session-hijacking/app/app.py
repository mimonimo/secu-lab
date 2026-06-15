"""
세션/쿠키 탈취 실습 - 자기완결형 교육용 Flask 앱.

가상의 커뮤니티 'TalkSpot'을 무대로, 저장형 XSS(Stored XSS)를 이용한
세션 쿠키 탈취와 세션 하이재킹을 체험한다.

안전/교육 설계:
- 완전 로컬/LAN 전용. 외부 전송 없음.
- 쿠키/계정/글은 모두 가짜이며 메모리에만 존재. 컨테이너 종료 시 소멸.
- '안전 모드' 토글로 같은 공격이 어떻게 막히는지(HttpOnly + 출력 인코딩) 바로 비교.

이 앱은 의도적으로 취약하게 만들어졌습니다. 방어 학습용이며,
이런 기법을 허락 없이 실제 서비스에 사용하는 것은 불법입니다.
"""
import html
import secrets
from collections import deque
from datetime import datetime

from flask import Flask, make_response, redirect, render_template, request, url_for

app = Flask(__name__)

# ---- 메모리 상태 (영구 저장 없음) ----
SESSIONS: dict[str, str] = {}          # token -> username
COMMENTS: deque = deque(maxlen=50)     # 방명록 글: {"author", "body", "time"}
STOLEN: deque = deque(maxlen=50)       # 탈취된 쿠키: {"time", "cookie", "ip"}
SAFE_MODE = {"on": False}              # 강사가 토글하는 방어 모드

# 가짜 사용자별 '비밀 정보' (하이재킹 피해를 실감나게)
SECRETS = {
    "alice": "💬 받은 쪽지 3건 · 💰 포인트 12,400P · 📵 비공개 게시글 2개",
    "bob": "💬 받은 쪽지 1건 · 💰 포인트 980P · 📵 비공개 게시글 5개",
    "teacher": "💬 받은 쪽지 9건 · 💰 포인트 99,999P · 📵 비공개 게시글 12개",
}


def current_user() -> str | None:
    token = request.cookies.get("sid")
    return SESSIONS.get(token) if token else None


@app.route("/")
def home():
    return render_template(
        "home.html",
        user=current_user(),
        safe_mode=SAFE_MODE["on"],
    )


@app.route("/login", methods=["POST"])
def login():
    username = (request.form.get("username") or "guest").strip().lower()[:20] or "guest"
    token = secrets.token_hex(8)
    SESSIONS[token] = username
    SECRETS.setdefault(username, "💬 받은 쪽지 0건 · 💰 포인트 100P")

    resp = make_response(redirect(url_for("board")))
    # 핵심 차이: 안전 모드면 HttpOnly+SameSite 로 JS 접근/유출 차단
    if SAFE_MODE["on"]:
        resp.set_cookie("sid", token, httponly=True, samesite="Strict")
    else:
        resp.set_cookie("sid", token)  # 취약: JS가 document.cookie 로 읽을 수 있음
    return resp


@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for("home")))
    resp.delete_cookie("sid")
    return resp


@app.route("/board")
def board():
    # 안전 모드면 출력 인코딩(이스케이프), 취약 모드면 원본 HTML 그대로 렌더 → XSS 발동
    rendered = []
    for c in list(COMMENTS):
        body = c["body"] if not SAFE_MODE["on"] else html.escape(c["body"])
        rendered.append({"author": html.escape(c["author"]), "body": body, "time": c["time"]})
    return render_template(
        "board.html",
        user=current_user(),
        comments=rendered,
        safe_mode=SAFE_MODE["on"],
    )


@app.route("/comment", methods=["POST"])
def comment():
    author = (request.form.get("author") or current_user() or "익명")[:20]
    body = (request.form.get("body") or "")[:2000]
    COMMENTS.appendleft({"author": author, "body": body, "time": datetime.now().strftime("%H:%M:%S")})
    return redirect(url_for("board"))


@app.route("/steal")
def steal():
    """공격자 수집 엔드포인트. XSS 페이로드가 여기로 쿠키를 보낸다 (로컬 전용)."""
    cookie = request.args.get("c", "")[:500]
    if cookie:
        STOLEN.appendleft(
            {"time": datetime.now().strftime("%H:%M:%S"), "cookie": cookie, "ip": request.remote_addr or "?"}
        )
    # 1x1 투명 응답 (실제 공격이 흔적을 안 남기려는 방식 시연)
    return ("", 204)


@app.route("/attacker")
def attacker():
    return render_template("attacker.html", stolen=list(STOLEN))


@app.route("/hijack", methods=["POST"])
def hijack():
    """탈취한 쿠키 문자열에서 sid 값을 꺼내 '내' 쿠키로 설정 → 피해자로 로그인된다."""
    raw = request.form.get("cookie", "")
    token = ""
    for part in raw.split(";"):
        part = part.strip()
        if part.startswith("sid="):
            token = part[len("sid="):]
            break
    if not token:
        token = raw.strip()  # 토큰만 붙여넣은 경우도 허용
    resp = make_response(redirect(url_for("mypage")))
    resp.set_cookie("sid", token)
    return resp


@app.route("/mypage")
def mypage():
    user = current_user()
    secret = SECRETS.get(user) if user else None
    return render_template("mypage.html", user=user, secret=secret)


@app.route("/mode", methods=["POST"])
def mode():
    SAFE_MODE["on"] = request.form.get("safe") == "on"
    return redirect(request.referrer or url_for("home"))


@app.route("/reset", methods=["POST"])
def reset():
    COMMENTS.clear()
    STOLEN.clear()
    return redirect(request.referrer or url_for("home"))


@app.route("/health")
def health():
    return {"status": "ok", "safe_mode": SAFE_MODE["on"]}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
