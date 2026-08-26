import io
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
except Exception:
    Document = None


st.set_page_config(
    page_title="구매 Case AI Agent PoC",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
    --bg: #F5F7FB;
    --card: #FFFFFF;
    --ink: #172033;
    --sub: #667085;
    --line: #E7EAF0;
    --accent: #4F46E5;
    --accent-soft: #EEF2FF;
    --good: #067647;
    --good-soft: #ECFDF3;
    --warn: #B54708;
    --warn-soft: #FFFAEB;
    --danger: #B42318;
    --danger-soft: #FEF3F2;
}
.stApp { background: var(--bg); }
.block-container { max-width: 1500px; padding-top: 1.2rem; padding-bottom: 2rem; }
h1, h2, h3 { color: var(--ink); letter-spacing: -0.02em; }
[data-testid="stSidebar"] { background: #101828; }
[data-testid="stSidebar"] * { color: #F9FAFB; }
[data-testid="stSidebar"] input { color: #101828 !important; }
.hero {
    background: linear-gradient(120deg, #111827 0%, #27306B 58%, #4F46E5 100%);
    color: white;
    padding: 22px 26px;
    border-radius: 18px;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(16,24,40,.12);
}
.hero .eyebrow { font-size: 12px; opacity: .72; letter-spacing: .12em; font-weight: 700; }
.hero .title { font-size: 28px; font-weight: 800; margin-top: 4px; letter-spacing: -.03em; }
.hero .desc { margin-top: 7px; opacity: .82; font-size: 14px; }
.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(16,24,40,.04);
    height: 100%;
}
.card-title {
    color: var(--ink);
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 12px;
}
.big-action {
    background: var(--accent-soft);
    border: 1px solid #C7D2FE;
    border-radius: 14px;
    padding: 16px 18px;
}
.big-action .label { color: #4338CA; font-size: 12px; font-weight: 800; }
.big-action .value { color: #312E81; font-size: 24px; font-weight: 900; margin-top: 3px; }
.mini {
    color: var(--sub);
    font-size: 12px;
}
.pill {
    display: inline-block;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    margin: 2px 3px 2px 0;
}
.pill-good { color: var(--good); background: var(--good-soft); }
.pill-warn { color: var(--warn); background: var(--warn-soft); }
.pill-danger { color: var(--danger); background: var(--danger-soft); }
.pill-neutral { color: #344054; background: #F2F4F7; }
.stage-wrap {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
    margin: 7px 0 4px;
}
.stage {
    border: 1px solid var(--line);
    background: #F8FAFC;
    padding: 10px 8px;
    border-radius: 10px;
    text-align: center;
    color: #667085;
    font-size: 12px;
    font-weight: 700;
}
.stage.done { background: var(--good-soft); color: var(--good); border-color: #ABEFC6; }
.stage.current { background: var(--accent-soft); color: #4338CA; border-color: #C7D2FE; box-shadow: inset 0 0 0 1px #A5B4FC; }
.rule {
    border-left: 4px solid #F79009;
    background: #FFFAEB;
    padding: 10px 12px;
    margin: 7px 0;
    border-radius: 8px;
    color: #7A2E0E;
    font-size: 13px;
}
.guide-row {
    display: grid;
    grid-template-columns: 120px 1fr;
    border-bottom: 1px solid var(--line);
    padding: 9px 0;
    font-size: 13px;
}
.guide-row:last-child { border-bottom: none; }
.guide-key { color: var(--sub); font-weight: 700; }
.guide-val { color: var(--ink); font-weight: 650; }
.evidence {
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 9px 11px;
    margin-bottom: 7px;
    background: #FCFCFD;
}
.evidence .name { color: var(--ink); font-weight: 800; font-size: 13px; }
.evidence .status { color: var(--sub); font-size: 12px; margin-top: 2px; }
.footer-note {
    color: #667085;
    font-size: 11px;
    margin-top: 14px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


ACTIONS = [
    "CHECK_DOCUMENT",
    "ASK_SUPPLIER",
    "CHECK_SUPPLIER_READY",
    "SEND_NEGOTIATION",
    "WAIT_REPLY",
    "PREPARE_APPROVAL",
    "PREPARE_CONTRACT",
    "BLOCK",
    "COMPLETE",
]

STAGES = ["기안검토", "근거확인", "공급사확인", "수의시담", "구매결재", "계약"]

ACTION_KO = {
    "CHECK_DOCUMENT": "서류 추가 확인",
    "ASK_SUPPLIER": "업체 단독수행 근거 확인",
    "CHECK_SUPPLIER_READY": "공급사 MDVAN·수수료 확인",
    "SEND_NEGOTIATION": "수의시담 발송 준비",
    "WAIT_REPLY": "업체 회신 대기",
    "PREPARE_APPROVAL": "구매결재 작성 준비",
    "PREPARE_CONTRACT": "계약작성 준비",
    "BLOCK": "진행 보류 / 확인 필요",
    "COMPLETE": "Case 완료",
}


@dataclass
class EvidenceSignals:
    purchase_doc: bool = False
    quote: bool = False
    exclusive_reason: bool = False
    mdvan_ready: bool = False
    fee_ready: bool = False
    quotation_ready: bool = False
    final_quote: bool = False


@dataclass
class Decision:
    state_code: str
    state_ko: str
    current_stage_index: int
    next_action: str
    reason: str
    missing: List[str]
    hard_rules: List[str]
    human_approval_required: bool = True


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_text(uploaded_file) -> str:
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    raw = uploaded_file.getvalue()

    try:
        if suffix == ".pdf" and PdfReader is not None:
            reader = PdfReader(io.BytesIO(raw))
            pages = [(page.extract_text() or "") for page in reader.pages[:40]]
            return "\n".join(pages)

        if suffix == ".docx" and Document is not None:
            doc = Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)

        if suffix in {".xlsx", ".xls"}:
            xls = pd.ExcelFile(io.BytesIO(raw))
            chunks = []
            for sheet in xls.sheet_names[:8]:
                df = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=200)
                chunks.append(f"[SHEET:{sheet}]\n" + df.fillna("").astype(str).to_csv(index=False, header=False))
            return "\n".join(chunks)

        if suffix in {".txt", ".md", ".csv"}:
            return raw.decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"[파일 읽기 오류: {name}] {exc}"

    return ""


def contains_any(text: str, keywords: List[str]) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)


def infer_signals(file_names: List[str], text: str) -> EvidenceSignals:
    source = clean_text(" ".join(file_names) + " " + text)

    return EvidenceSignals(
        purchase_doc=contains_any(
            source,
            ["구매기안", "구매 의뢰", "구매의뢰", "구매요청", "구매 요청", "기안"],
        ),
        quote=contains_any(source, ["견적서", "quotation", "quote", "견적"]),
        exclusive_reason=contains_any(
            source,
            [
                "당사만", "당사 밖에", "당사밖에", "단독 수행", "단독수행",
                "유일", "독점", "타사 수행 불가", "타업체 수행 불가",
                "본인들밖에", "해당 업체만", "해당업체만",
            ],
        ),
        mdvan_ready=contains_any(
            source,
            ["mdvan 가입 가능", "mdvan가입 가능", "가입가능", "가입 가능", "공급사 등록 가능"],
        ),
        fee_ready=contains_any(
            source,
            ["수수료 수용", "수수료 허용", "수수료 적용 가능", "수수료 가능", "수수료 확인"],
        ),
        quotation_ready=contains_any(
            source,
            ["견적 가능", "견적 제출 가능", "견적제출 가능", "견적 진행", "견적 제출"],
        ),
        final_quote=contains_any(
            source,
            ["최종견적", "최종 견적", "최종 견적서", "final quotation", "final quote"],
        ),
    )


def demo_signals(step: int) -> EvidenceSignals:
    if step == 1:
        return EvidenceSignals(purchase_doc=True, quote=True)
    if step == 2:
        return EvidenceSignals(purchase_doc=True, quote=True, exclusive_reason=True)
    if step == 3:
        return EvidenceSignals(
            purchase_doc=True,
            quote=True,
            exclusive_reason=True,
            mdvan_ready=True,
            fee_ready=True,
            quotation_ready=True,
        )
    return EvidenceSignals(
        purchase_doc=True,
        quote=True,
        exclusive_reason=True,
        mdvan_ready=True,
        fee_ready=True,
        quotation_ready=True,
        final_quote=True,
    )


def make_decision(signals: EvidenceSignals, purchase_type: str) -> Decision:
    hard_rules = [
        "AI가 구매유형을 임의로 변경하지 않습니다.",
        "MDVAN 발송·계약상신 등 실제 실행은 담당자 확인 후 진행합니다.",
    ]
    if purchase_type == "일반":
        hard_rules.append(
            "일반구매로 기안된 건은 사후 단수·긴급 근거만으로 AI가 구매유형을 변경하지 않습니다."
        )

    if not signals.purchase_doc and not signals.quote:
        return Decision(
            "DOCUMENT_REQUIRED",
            "기초 서류 확인 필요",
            0,
            "CHECK_DOCUMENT",
            "구매기안 또는 견적 근거가 확인되지 않아 Case 판단을 시작하기 어렵습니다.",
            ["구매기안 또는 구매요청 자료", "기존 견적자료"],
            hard_rules,
        )

    if not signals.exclusive_reason:
        return Decision(
            "SUPPLIER_EVIDENCE_REQUIRED",
            "단일 공급사 근거 확인 필요",
            1,
            "ASK_SUPPLIER",
            "특정 공급사 견적은 확인되지만, 왜 해당 업체 중심으로 진행해야 하는지 근거가 아직 확인되지 않았습니다.",
            ["해당 업체만 수행 가능한 사유", "가능하면 업체의 서면 근거"],
            hard_rules,
        )

    if not (signals.mdvan_ready and signals.fee_ready and signals.quotation_ready):
        missing = []
        if not signals.mdvan_ready:
            missing.append("MDVAN 가입/등록 가능 여부")
        if not signals.fee_ready:
            missing.append("수수료 적용 수용 여부")
        if not signals.quotation_ready:
            missing.append("견적 제출 가능 여부")
        return Decision(
            "SUPPLIER_READY_CHECK",
            "공급사 진행조건 확인",
            2,
            "CHECK_SUPPLIER_READY",
            "단일 공급사 진행 근거는 확보되었습니다. 수의시담 전에 공급사가 MDVAN·수수료·견적 제출 조건을 충족하는지 확인해야 합니다.",
            missing,
            hard_rules,
        )

    if not signals.final_quote:
        return Decision(
            "READY_FOR_NEGOTIATION",
            "수의시담 진행 가능",
            3,
            "SEND_NEGOTIATION",
            "단일 공급사 근거와 공급사 진행조건이 확인되어 다음 단계로 수의시담 발송 준비가 가능합니다.",
            [],
            hard_rules,
        )

    return Decision(
        "NEGOTIATION_RESULT_RECEIVED",
        "견적 회신 확인",
        4,
        "PREPARE_APPROVAL",
        "최종 견적이 확인되어 가격비교 및 구매결재 작성 단계로 이동할 수 있습니다.",
        [],
        hard_rules,
    )


def llm_decision(
    case_id: str,
    purchase_type: str,
    signals: EvidenceSignals,
    extracted_text: str,
    deterministic: Decision,
    api_key: str,
    model: str,
) -> Optional[Dict]:
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    client = OpenAI(api_key=api_key)
    evidence_text = clean_text(extracted_text)[:18000]

    system = """
당신은 의료 GPO 구매 Case의 Next Action Selector다.
목표는 Case의 현재 상태와 증빙을 보고 허용된 Action 중 다음 행동 하나를 고르는 것이다.
회사 규칙과 deterministic guardrail은 절대로 변경하거나 우회하지 않는다.
구매유형, 금액, 수수료율처럼 명시적 규칙이 필요한 값은 추정하지 않는다.
MDVAN을 실제 클릭하거나 발송한 것처럼 말하지 않는다.
출력은 JSON만 반환한다.
"""

    user = f"""
Case ID: {case_id}
구매유형: {purchase_type}
허용 Action: {ACTIONS}
기본 Rule Engine 판단:
- state: {deterministic.state_code}
- next_action: {deterministic.next_action}
- reason: {deterministic.reason}
- hard_rules: {deterministic.hard_rules}

증빙 signal:
{signals.__dict__}

문서 추출 텍스트:
{evidence_text}

다음 JSON 형식으로 답하라.
{{
  "next_action": "허용 Action 중 하나",
  "reason": "한국어 2~3문장",
  "evidence_summary": ["확인된 근거 1", "확인된 근거 2"],
  "missing": ["추가 확인 필요사항"],
  "risk_note": "업무상 주의사항"
}}

Rule Engine의 hard rule과 충돌한다면 반드시 Rule Engine을 우선한다.
"""

    response = client.responses.create(
        model=model,
        store=False,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    raw = response.output_text.strip()
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return None
    parsed = json.loads(match.group(0))
    if parsed.get("next_action") not in ACTIONS:
        return None
    return parsed


def mdvan_guide(action: str, supplier_name: str) -> List[tuple]:
    supplier = supplier_name or "해당 공급사"

    mapping = {
        "CHECK_DOCUMENT": [
            ("현재 MDVAN 작업", "아직 입력하지 않음"),
            ("먼저 확인", "구매기안·견적자료 확보 후 Case를 재분석"),
            ("담당자 액션", "기초자료를 업로드하고 AI Agent를 다시 실행"),
        ],
        "ASK_SUPPLIER": [
            ("현재 MDVAN 작업", "아직 발송하지 않음"),
            ("업체 확인", f"{supplier}만 수행 가능한 이유와 서면 근거 요청"),
            ("추가 확인", "MDVAN 가입 가능 여부, 수수료 수용 여부, 견적 참여 가능 여부"),
        ],
        "CHECK_SUPPLIER_READY": [
            ("현재 MDVAN 작업", "수의시담 발송 전 사전 확인"),
            ("공급사", supplier),
            ("확인사항", "MDVAN 가입/등록 가능 여부"),
            ("확인사항", "해당 구매유형 수수료 수용 여부"),
            ("확인사항", "견적 제출 가능 시점"),
        ],
        "SEND_NEGOTIATION": [
            ("메뉴", "MDVAN > 수의시담/가격조사 발송 화면"),
            ("공급사", supplier),
            ("첨부자료", "구매요청 관련 자료 및 견적에 필요한 사양/첨부"),
            ("이지메모", "해당 구매 건 관련 수의시담 요청드립니다. 첨부자료 확인 후 견적 제출 부탁드립니다."),
            ("최종 확인", "공급사·첨부·수수료 조건 확인 후 담당자가 발송"),
        ],
        "WAIT_REPLY": [
            ("현재 상태", "업체 견적 회신 대기"),
            ("담당자 액션", "회신 도착 시 최종 견적을 Evidence로 추가"),
        ],
        "PREPARE_APPROVAL": [
            ("메뉴", "구매결재 작성 화면"),
            ("가격검토", "종전가격/기초가격/최종견적 등 적용 가능한 근거로 비교"),
            ("작성", "9. 가격조사기준 및 10. 특이사항 정리"),
            ("최종 확인", "금액·수수료·계약방법을 담당자가 검증 후 상신"),
        ],
    }
    return mapping.get(action, [("담당자 확인", "해당 단계의 업무 절차 확인 필요")])


def evidence_rows(signals: EvidenceSignals) -> List[tuple]:
    return [
        ("구매기안/요청자료", signals.purchase_doc),
        ("기존 견적", signals.quote),
        ("단일 공급사 근거", signals.exclusive_reason),
        ("MDVAN 가입/등록 가능", signals.mdvan_ready),
        ("수수료 수용", signals.fee_ready),
        ("견적 제출 가능", signals.quotation_ready),
        ("최종 견적", signals.final_quote),
    ]


def render_stage(current_index: int):
    html = '<div class="stage-wrap">'
    for idx, stage in enumerate(STAGES):
        cls = "stage"
        if idx < current_index:
            cls += " done"
        elif idx == current_index:
            cls += " current"
        html += f'<div class="{cls}">{stage}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_evidence(signals: EvidenceSignals):
    for name, ok in evidence_rows(signals):
        mark = "확인" if ok else "미확인"
        cls = "pill-good" if ok else "pill-neutral"
        st.markdown(
            f"""
            <div class="evidence">
              <div class="name">{name}</div>
              <div class="status"><span class="pill {cls}">{mark}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">HUMAN-IN-THE-LOOP PROCUREMENT AGENT · POC</div>
      <div class="title">구매 Case AI Agent</div>
      <div class="desc">서류를 관찰하고 현재 업무상태를 판단하여 다음 Action과 MDVAN 처리방법을 제안합니다.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Case 설정")
    case_id = st.text_input("Case 번호", value="KDWEZ202600338")
    supplier_name = st.text_input("공급사", value="소프트인")
    purchase_type = st.selectbox("구매기안 유형", ["일반", "단수", "긴급"], index=0)

    st.markdown("---")
    demo_mode = st.toggle("발표 데모 모드", value=True)
    if demo_mode:
        demo_step = st.radio(
            "시연 단계",
            [
                "1. 최초 기안 검토",
                "2. 단독 수행 근거 확보",
                "3. 공급사 진행조건 확인 완료",
                "4. 최종 견적 회신",
            ],
            index=0,
        )
    else:
        demo_step = None

    st.markdown("---")
    st.markdown("### 실제 문서 업로드")
    uploads = st.file_uploader(
        "구매기안·견적·업체회신 등",
        type=["pdf", "docx", "xlsx", "xls", "txt", "md", "csv"],
        accept_multiple_files=True,
        help="Case 번호는 문서에서 찾지 못해도 됩니다. 화면에서 별도로 입력합니다.",
    )

    st.markdown("---")
    st.markdown("### 선택: LLM 판단 연결")
    use_llm = st.toggle("LLM Next Action Selector 사용", value=False)
    api_key = ""
    model = "gpt-5"
    if use_llm:
        st.caption("회사 보안정책 확인 전 실제 내부문서의 외부 API 전송은 피하세요.")
        api_key = st.text_input("OPENAI_API_KEY", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-5"))

    run_button = st.button("AI Agent 분석 시작", type="primary", use_container_width=True)


file_names = [f.name for f in uploads] if uploads else []
extracted_chunks = []
if uploads:
    for f in uploads:
        extracted_chunks.append(f"\n[FILE: {f.name}]\n{extract_text(f)}")
extracted_text = "\n".join(extracted_chunks)

if demo_mode:
    demo_step_num = int(demo_step.split(".")[0])
    signals = demo_signals(demo_step_num)
else:
    signals = infer_signals(file_names, extracted_text)

decision = make_decision(signals, purchase_type)

llm_result = None
if run_button and use_llm and api_key:
    with st.spinner("LLM이 Evidence와 Rule Guardrail을 함께 검토하고 있습니다..."):
        try:
            llm_result = llm_decision(
                case_id,
                purchase_type,
                signals,
                extracted_text,
                decision,
                api_key,
                model,
            )
        except Exception as exc:
            st.warning(f"LLM 호출에 실패하여 Rule Engine 결과로 표시합니다: {exc}")

effective_action = decision.next_action
effective_reason = decision.reason
missing = decision.missing
risk_note = "최종 발송·상신은 담당자 확인 후 진행합니다."

if llm_result:
    # Hard Guardrail은 deterministic engine이 유지하고 LLM은 허용 Action 범위에서만 해석한다.
    effective_action = llm_result.get("next_action", decision.next_action)
    effective_reason = llm_result.get("reason", decision.reason)
    missing = llm_result.get("missing", decision.missing)
    risk_note = llm_result.get("risk_note", risk_note)


header_left, header_mid, header_right = st.columns([1.2, 1, 1])
with header_left:
    st.metric("Case", case_id or "미입력")
with header_mid:
    st.metric("현재 상태", decision.state_ko)
with header_right:
    confirmed = sum(1 for _, ok in evidence_rows(signals) if ok)
    st.metric("근거 충족", f"{confirmed}/7")

st.markdown("### 업무 진행 상태")
render_stage(decision.current_stage_index)

left, right = st.columns([1.25, 1], gap="large")

with left:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">AGENT DECISION</div>
          <div class="big-action">
            <div class="label">NEXT ACTION</div>
            <div class="value">{ACTION_KO.get(effective_action, effective_action)}</div>
            <div class="mini">{effective_action}</div>
          </div>
          <div style="margin-top:14px;color:#172033;font-weight:800;font-size:13px;">판단 이유</div>
          <div style="margin-top:6px;color:#475467;font-size:14px;line-height:1.65;">{effective_reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### MDVAN / 담당자 처리 가이드")
    guide_html = '<div class="card">'
    for key, value in mdvan_guide(effective_action, supplier_name):
        guide_html += (
            f'<div class="guide-row"><div class="guide-key">{key}</div>'
            f'<div class="guide-val">{value}</div></div>'
        )
    guide_html += "</div>"
    st.markdown(guide_html, unsafe_allow_html=True)

with right:
    st.markdown('<div class="card-title">EVIDENCE CHECK</div>', unsafe_allow_html=True)
    render_evidence(signals)

    if missing:
        st.markdown("#### 추가 확인 필요")
        for item in missing:
            st.markdown(f"- **{item}**")

    st.markdown("#### Guardrail")
    for rule in decision.hard_rules:
        st.markdown(f'<div class="rule">{rule}</div>', unsafe_allow_html=True)

    st.markdown("#### Human-in-the-loop")
    st.markdown(
        f'<span class="pill pill-warn">담당자 승인 필요</span> <span class="mini">{risk_note}</span>',
        unsafe_allow_html=True,
    )


with st.expander("Agent가 읽은 문서 / 기술 로그", expanded=False):
    if file_names:
        st.write("업로드 파일:", file_names)
    else:
        st.write("업로드된 실제 파일 없음 — 발표 데모 State를 사용 중입니다.")

    st.json(
        {
            "case_id": case_id,
            "state": decision.state_code,
            "signals": signals.__dict__,
            "rule_engine_action": decision.next_action,
            "effective_action": effective_action,
            "llm_used": bool(llm_result),
        }
    )
    if extracted_text:
        st.text_area("추출 텍스트 미리보기", extracted_text[:12000], height=220)

st.markdown(
    """
    <div class="footer-note">
    PoC 범위: 문서 관찰 → State 생성 → Rule Guardrail → Next Action 선택 → MDVAN 처리 가이드.
    MDVAN 자동 클릭·발송·계약상신은 포함하지 않습니다.
    </div>
    """,
    unsafe_allow_html=True,
)
