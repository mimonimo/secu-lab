"""
사이트 복제 인식 실습 - 자기완결형 교육용 Flask 앱.

가상 브랜드 '한빛은행'을 무대로:
1) 웹사이트의 겉모습(HTML/CSS)은 누구나 복제할 수 있음을 시연
2) 그래서 '겉모습'이 아니라 도메인/인증서/유입경로로 진짜를 가려야 함을 교육
3) 식별 퀴즈로 마무리

안전 설계: 완전 로컬, 실제 은행/서비스 사칭 아님(가상 브랜드), 자격증명 수집 없음.
복제는 '같은 화면을 다른 가짜 주소로 보여주기'만으로 시연한다.
"""
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
