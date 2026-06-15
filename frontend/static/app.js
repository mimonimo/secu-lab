// secu-lab 프론트엔드 제어 스크립트
(function () {
  "use strict";

  const STATUS_LABEL = {
    running: { text: "실행 중", cls: "bg-emerald-500/20 text-emerald-300" },
    stopped: { text: "정지", cls: "bg-slate-800 text-slate-400" },
    unavailable: { text: "Docker 미실행", cls: "bg-amber-500/20 text-amber-300" },
    "n/a": { text: "수동", cls: "bg-slate-800 text-slate-500" },
    loading: { text: "확인 중…", cls: "bg-slate-800 text-slate-500" },
  };

  function applyStatus(badge, status) {
    const s = STATUS_LABEL[status] || STATUS_LABEL["n/a"];
    badge.textContent = s.text;
    badge.className =
      "status-badge text-[11px] px-2 py-0.5 rounded-full " + s.cls;
  }

  async function fetchStatus(id) {
    try {
      const r = await fetch(`/api/module/${id}/status`);
      if (!r.ok) return "unavailable";
      const data = await r.json();
      return data.status || "unavailable";
    } catch (e) {
      return "unavailable";
    }
  }

  async function refresh(scope) {
    const id = scope.dataset.moduleId;
    if (!id) return;
    const badge = scope.querySelector(".status-badge");
    if (badge) applyStatus(badge, await fetchStatus(id));
  }

  async function action(id, verb, scope) {
    const msg = scope.querySelector(".action-msg");
    const buttons = scope.querySelectorAll(".btn-start, .btn-stop");
    buttons.forEach((b) => (b.disabled = true));
    if (msg) msg.textContent = verb === "start" ? "시작 중… (최초 실행 시 이미지 다운로드로 시간이 걸릴 수 있어요)" : "종료 중…";
    try {
      const r = await fetch(`/api/module/${id}/${verb}`, { method: "POST" });
      const data = await r.json();
      if (msg) msg.textContent = data.message || "";
    } catch (e) {
      if (msg) msg.textContent = "요청 실패: " + e.message;
    } finally {
      buttons.forEach((b) => (b.disabled = false));
      await refresh(scope);
    }
  }

  function wire(scope) {
    const id = scope.dataset.moduleId;
    if (!id) return;
    const startBtn = scope.querySelector(".btn-start");
    const stopBtn = scope.querySelector(".btn-stop");
    if (startBtn) startBtn.addEventListener("click", () => action(id, "start", scope));
    if (stopBtn) stopBtn.addEventListener("click", () => action(id, "stop", scope));
    refresh(scope);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const scopes = document.querySelectorAll("[data-module-id]");
    scopes.forEach(wire);
    // 10초마다 상태 자동 갱신
    setInterval(() => scopes.forEach(refresh), 10000);
  });
})();
