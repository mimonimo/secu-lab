// secu-lab 수업 타이머 위젯
(function () {
  "use strict";

  let total = 10 * 60;   // 설정된 총 시간(초)
  let remaining = total; // 남은 시간(초)
  let ticking = null;    // setInterval 핸들

  const $ = (id) => document.getElementById(id);

  function fmt(sec) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function render() {
    const disp = $("timer-display");
    if (!disp) return;
    disp.textContent = fmt(remaining);
    // 색상: 1분 이하 경고, 종료 시 빨강
    if (remaining === 0) disp.className = "text-center text-4xl font-mono font-bold tracking-tight my-2 text-rose-500 animate-pulse";
    else if (remaining <= 60) disp.className = "text-center text-4xl font-mono font-bold tracking-tight my-2 text-amber-400";
    else disp.className = "text-center text-4xl font-mono font-bold tracking-tight my-2 text-slate-100";
  }

  function beep() {
    // 외부 리소스 없이 WebAudio로 종료음 (브라우저 자체 기능)
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = 880; o.type = "sine";
      g.gain.setValueAtTime(0.25, ctx.currentTime);
      o.start();
      o.stop(ctx.currentTime + 0.6);
    } catch (e) { /* 오디오 미지원 시 무시 */ }
  }

  function stop() {
    if (ticking) { clearInterval(ticking); ticking = null; }
    const btn = $("timer-start");
    if (btn) { btn.textContent = "시작"; btn.classList.remove("bg-amber-600", "hover:bg-amber-500"); btn.classList.add("bg-emerald-600", "hover:bg-emerald-500"); }
  }

  function start() {
    if (ticking) { // 일시정지
      stop();
      return;
    }
    if (remaining <= 0) remaining = total;
    const btn = $("timer-start");
    if (btn) { btn.textContent = "일시정지"; btn.classList.remove("bg-emerald-600", "hover:bg-emerald-500"); btn.classList.add("bg-amber-600", "hover:bg-amber-500"); }
    ticking = setInterval(() => {
      remaining = Math.max(0, remaining - 1);
      render();
      if (remaining === 0) { stop(); beep(); }
    }, 1000);
  }

  function reset() {
    stop();
    remaining = total;
    render();
  }

  function setPreset(min) {
    total = min * 60;
    reset();
  }

  document.addEventListener("DOMContentLoaded", () => {
    render();
    const startBtn = $("timer-start");
    const resetBtn = $("timer-reset");
    if (startBtn) startBtn.addEventListener("click", start);
    if (resetBtn) resetBtn.addEventListener("click", reset);
    document.querySelectorAll(".timer-preset").forEach((b) => {
      b.addEventListener("click", () => setPreset(parseInt(b.dataset.min, 10)));
    });
    // 접기/펼치기
    const collapse = $("timer-collapse");
    const body = $("timer-body");
    if (collapse && body) {
      collapse.addEventListener("click", () => {
        const hidden = body.style.display === "none";
        body.style.display = hidden ? "" : "none";
        collapse.textContent = hidden ? "─" : "+";
      });
    }
  });
})();
