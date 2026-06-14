from __future__ import annotations

import html
from typing import Any

import streamlit as st

import api

ASSET_OPTIONS = [
    "무기체계 설계도면",
    "소스코드",
    "인사·계약정보",
    "시험데이터",
    "네트워크 인프라",
    "문서·산출물",
]
INCIDENT_THREATS = ["APT 표적공격", "랜섬웨어", "공급망 침해", "내부자 유출", "물리적 침입", "피싱"]
PREVENTIVE_THREATS = ["내부자 유출", "APT 표적공격", "공급망 침해", "물리적 침입", "랜섬웨어"]
DAMAGE_FLAGS = ["데이터 유출 정황", "시스템 다운", "확산 중", "외부 신고 필요"]
ORG_SIZES = ["중소협력사", "연구소", "대기업"]
SECURITY_LEVELS = ["매우 낮음", "낮음", "보통", "높음", "매우 높음"]
REGULATIONS = ["방위산업기술보호법", "군사기밀보호", "ISMS", "없음"]
CASE_STATUSES = ["접수", "분석중", "조치중", "분석완료", "완료"]


def risk_color(level: str) -> str:
    return {"HIGH": "#f87171", "MEDIUM": "#fbbf24", "LOW": "#34d399"}.get(level, "#34d399")


def brand_header() -> None:
    st.markdown(
        """
        <div class="df-brand">
          <div class="ko">일단막아</div>
          <div class="en">D E F E N S E&nbsp;&nbsp;F I R S T</div>
          <div class="sub">방위산업 실무자를 위한 보안 위협 대응책 추천 시스템</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- 로그인

def login_view() -> None:
    brand_header()
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 4, 1])
    with center:
        st.subheader("부서 워크스페이스 로그인")
        with st.form("login_form"):
            code = st.text_input("부서 코드", placeholder="예: DAPA-OPS")
            name = st.text_input("실무자 이름", placeholder="예: 홍길동")
            submitted = st.form_submit_button("워크스페이스 접속", type="primary", use_container_width=True)
        if submitted:
            data = api.request("POST", "/auth/login",
                               json={"department_code": code, "operator_name": name})
            if data:
                st.session_state.user = data
                st.rerun()
        st.write("")
        st.info(
            "**데모용 등록 부서 코드**\n\n"
            "- `DAPA-OPS` · 방산보안대응팀\n"
            "- `RND-LAB` · 무기체계연구소\n"
            "- `SUPPLY-7` · 협력업체보안실"
        )
        st.caption("같은 부서 코드로 접속한 실무자는 동일한 케이스 목록·상태·메모를 공유합니다.")


def sidebar(user: dict[str, Any]) -> str:
    with st.sidebar:
        st.markdown("### 🛡️ 워크스페이스")
        st.write(f"부서 **{user['department_name']}**")
        st.write(f"코드 `{user['department_code']}`")
        st.write(f"실무자 **{user['operator_name']}**")
        st.divider()
        nav = st.radio("메뉴", ["🔍 새 진단", "🗂️ 부서 공유 케이스"], label_visibility="collapsed")
        st.divider()
        st.caption(f"API · `{api.API_URL}`")
        if st.button("로그아웃", use_container_width=True):
            for k in ("user", "wiz", "latest_result", "latest_case"):
                st.session_state.pop(k, None)
            st.rerun()
    return nav


# ---------------------------------------------------------------- 위저드

def _incident_steps() -> list[dict[str, Any]]:
    return [
        {"key": "threat_type", "kind": "single", "q": "무슨 일이 일어났나요?",
         "help": "감지된 침해 유형을 선택하세요", "options": INCIDENT_THREATS},
        {"key": "asset", "kind": "single", "q": "어떤 자산이 영향을 받았나요?",
         "help": "침해된 자산의 민감도에 따라 위험도가 달라집니다", "options": ASSET_OPTIONS},
        {"key": "damage_flags", "kind": "multi", "q": "현재 피해 상황은?",
         "help": "해당하는 항목을 모두 선택하세요 (없으면 비워두고 다음)", "options": DAMAGE_FLAGS},
        {"key": "__env__", "kind": "env", "q": "조직 환경을 알려주세요",
         "help": "조직 규모와 현재 보안 수준에 따라 대응 우선순위가 조정됩니다"},
    ]


def _preventive_steps() -> list[dict[str, Any]]:
    return [
        {"key": "asset", "kind": "single", "q": "무엇을 지키고 싶나요?",
         "help": "보호하려는 핵심 자산을 선택하세요", "options": ASSET_OPTIONS},
        {"key": "concerns", "kind": "multi", "q": "우려되는 위협은?",
         "help": "대비하고 싶은 위협을 모두 선택하세요", "options": PREVENTIVE_THREATS},
        {"key": "__env__", "kind": "env", "q": "조직 환경을 알려주세요",
         "help": "조직 규모와 현재 보안 수준에 따라 강화 대책이 달라집니다"},
        {"key": "regulations", "kind": "multi", "q": "규제 준수 대상은?",
         "help": "적용받는 규제를 선택하세요 (복수 선택 가능)", "options": REGULATIONS},
    ]


def _multi_select(label: str, options: list[str], default: list[str], key: str) -> list[str]:
    if hasattr(st, "pills"):
        sel = st.pills(label, options, selection_mode="multi",
                       default=default, key=key, label_visibility="collapsed")
        return list(sel or [])
    chosen: list[str] = []
    cols = st.columns(3)
    for i, opt in enumerate(options):
        if cols[i % 3].checkbox(opt, value=opt in default, key=f"{key}_{i}"):
            chosen.append(opt)
    return chosen


def _progress_bar(step: int, total: int, mode_label: str) -> None:
    cells = "".join(f'<div class="{"on" if i < step else ""}"></div>' for i in range(total))
    st.markdown(f'<div class="df-step">STEP {step} / {total} · {mode_label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="df-bar">{cells}</div>', unsafe_allow_html=True)


def branch_view() -> None:
    brand_header()
    st.markdown("<div style='height:56px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="df-ask">지금 어떤 상황이신가요?</div>', unsafe_allow_html=True)

    _, left, _gap, right, _ = st.columns([1, 5, 0.6, 5, 1])
    with left:
        st.markdown(
            """<div class="df-branch-card alert"><h3>🚨 공격·사고가 발생했어요</h3>
            <p>침해 상황을 입력하면 긴급 대응 우선순위와 즉시 조치 대응책을 추천합니다.</p></div>""",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("사고대응 모드 시작", type="primary", use_container_width=True, key="b_inc"):
            st.session_state.wiz = {"mode": "incident", "step": 1, "answers": {}}
            st.session_state.pop("latest_result", None)
            st.rerun()
    with right:
        st.markdown(
            """<div class="df-branch-card guard"><h3>🛡️ 사전에 대비하고 싶어요</h3>
            <p>보호 자산과 환경을 입력하면 위험도를 진단하고 강화 대책을 추천합니다.</p></div>""",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("예방점검 모드 시작", use_container_width=True, key="b_prev"):
            st.session_state.wiz = {"mode": "preventive", "step": 1, "answers": {}}
            st.session_state.pop("latest_result", None)
            st.rerun()


def wizard_view(user: dict[str, Any]) -> None:
    wiz = st.session_state.wiz
    mode = wiz["mode"]
    steps = _incident_steps() if mode == "incident" else _preventive_steps()
    total = len(steps)
    step = wiz["step"]
    mode_label = "사고대응 모드" if mode == "incident" else "예방점검 모드"
    answers = wiz["answers"]
    cfg = steps[step - 1]

    st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        _progress_bar(step, total, mode_label)
        st.markdown(f'<div class="df-q">{cfg["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="df-help">{cfg["help"]}</div>', unsafe_allow_html=True)

        if cfg["kind"] == "single":
            opts = cfg["options"]
            prev = answers.get(cfg["key"])
            idx = opts.index(prev) if prev in opts else 0
            answers[cfg["key"]] = st.radio(cfg["q"], opts, index=idx,
                                           key=f"st_{mode}_{step}", label_visibility="collapsed")
        elif cfg["kind"] == "multi":
            answers[cfg["key"]] = _multi_select(cfg["q"], cfg["options"],
                                                answers.get(cfg["key"], []), f"mt_{mode}_{step}")
        elif cfg["kind"] == "env":
            c1, c2 = st.columns(2)
            answers["org_size"] = c1.selectbox("조직 규모", ORG_SIZES,
                                                index=ORG_SIZES.index(answers.get("org_size", "중소협력사")),
                                                key=f"org_{mode}")
            answers["security_level"] = c2.select_slider("현재 보안 수준", SECURITY_LEVELS,
                                                         value=answers.get("security_level", "보통"),
                                                         key=f"sec_{mode}")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    back, nxt = st.columns(2)
    with back:
        if st.button("← 이전" if step > 1 else "← 모드 선택", use_container_width=True):
            if step > 1:
                wiz["step"] = step - 1
            else:
                st.session_state.pop("wiz", None)
            st.rerun()
    with nxt:
        is_last = step == total
        label = "🔍 분석하기" if (is_last and mode == "incident") else "🔍 진단하기" if is_last else "다음 →"
        if st.button(label, type="primary", use_container_width=True):
            if is_last:
                _run_analysis(user, mode, answers)
            else:
                wiz["step"] = step + 1
                st.rerun()


def _run_analysis(user: dict[str, Any], mode: str, answers: dict[str, Any]) -> None:
    with st.spinner("위험도를 분석하는 중..."):
        data = api.request("POST", "/recommend", json={
            "department_id": user["department_id"],
            "operator_id": user["operator_id"],
            "mode": mode,
            "answers": answers,
        })
    if data:
        st.session_state.latest_result = data["result"]
        st.session_state.latest_case = data["case"]
        st.session_state.pop("wiz", None)
        st.rerun()


# ---------------------------------------------------------------- 결과

def render_result(result: dict[str, Any]) -> None:
    score = int(result["risk_score"])
    level = result["risk_level"]
    color = risk_color(level)
    threat = html.escape(str(result.get("threat_category", "")))
    priority = html.escape(str(result.get("priority", "")))
    st.markdown(
        f"""
        <div class="gauge-wrap">
          <div class="gauge-top">
            <div class="gauge-score" style="color:{color}">{score}<small> / 100</small></div>
            <div class="gauge-lvl" style="color:{color}">{level} RISK · 우선순위 {priority}</div>
          </div>
          <div class="gauge-bar"><i style="width:{score}%;background:{color}"></i></div>
          <div class="gauge-meta"><div>위협 등급 <b>{threat}</b></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(result.get("summary", ""))

    st.markdown("#### 📋 추천 대응책")
    for i, item in enumerate(result["recommendations"], 1):
        title = html.escape(str(item.get("title", "")))
        rtype = html.escape(str(item.get("type", "")))
        detail = html.escape(str(item.get("detail", "")))
        st.markdown(
            f"""<div class="rec"><span class="rt">{i}. {title}</span>
            <span class="badge">{rtype}</span><div class="rd">{detail}</div></div>""",
            unsafe_allow_html=True,
        )

    regs = html.escape(", ".join(result.get("regulations", [])) or "내부 보안규정")
    st.markdown(f'<div class="reg-box">⚖️ 관련 규제 · <b>{regs}</b></div>', unsafe_allow_html=True)


def new_diagnosis_view(user: dict[str, Any]) -> None:
    if "latest_result" in st.session_state:
        st.markdown("### 🔎 위협 진단 결과")
        case = st.session_state.get("latest_case")
        if case:
            st.success(f"부서 케이스 #{case['id']} 로 저장되었습니다.")
        render_result(st.session_state.latest_result)
        if st.button("➕ 새 진단 시작", type="primary"):
            st.session_state.pop("latest_result", None)
            st.session_state.pop("latest_case", None)
            st.rerun()
        return

    if "wiz" in st.session_state:
        wizard_view(user)
    else:
        branch_view()


# ---------------------------------------------------------------- 공유 케이스

def shared_cases_view(user: dict[str, Any]) -> None:
    st.markdown("### 🗂️ 부서 공유 케이스")
    data = api.request("GET", f"/departments/{user['department_id']}/cases")
    if not data:
        return
    cases = data["cases"]
    if not cases:
        st.info("아직 이 부서에 저장된 케이스가 없습니다. '새 진단'에서 첫 케이스를 만들어 보세요.")
        return

    labels = [f"#{c['id']} · {c['result']['threat_category']} · {c['status']} · {c['created_by_name']}"
              for c in cases]
    sel = st.selectbox("케이스 선택", labels)
    case = cases[labels.index(sel)]

    left, right = st.columns([1.3, 1])
    with left:
        st.caption(f"생성자 {case['created_by_name']} · {case['created_at']}")
        render_result(case["result"])
    with right:
        st.markdown("#### 공동 대응 상태")
        cur = case["status"] if case["status"] in CASE_STATUSES else "분석완료"
        new_status = st.selectbox("상태", CASE_STATUSES, index=CASE_STATUSES.index(cur))
        if st.button("상태 업데이트", use_container_width=True):
            if api.request("PATCH", f"/cases/{case['id']}/status",
                           json={"department_id": user["department_id"], "status": new_status}):
                st.success("상태가 업데이트되었습니다.")
                st.rerun()

        st.markdown("#### 대응 메모")
        note = st.text_area("메모 추가", placeholder="예: EDR 로그 확보 완료", label_visibility="collapsed")
        if st.button("메모 저장", use_container_width=True):
            if not note.strip():
                st.warning("메모 내용을 입력하세요.")
            elif api.request("POST", f"/cases/{case['id']}/notes",
                             json={"department_id": user["department_id"],
                                   "operator_id": user["operator_id"], "note": note}):
                st.success("메모가 저장되었습니다.")
                st.rerun()

        notes = api.request("GET", f"/cases/{case['id']}/notes",
                            params={"department_id": user["department_id"]})
        if notes and notes["notes"]:
            st.divider()
            for n in notes["notes"]:
                st.caption(f"{n['created_at']} · {n['operator_name']}")
                st.write(n["note"])
