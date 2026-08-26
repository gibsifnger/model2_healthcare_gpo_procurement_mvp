import io
import json
import os
import re
import zipfile
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional, Tuple

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

st.set_page_config(page_title="구매 Case AI Agent PoC", page_icon="◈", layout="wide")

st.markdown(
    """
<style>
.stApp{background:#F4F6FA}.block-container{max-width:1480px;padding-top:1.1rem}
[data-testid="stSidebar"]{background:#101828}[data-testid="stSidebar"] *{color:#F9FAFB}
[data-testid="stSidebar"] input{color:#101828!important}
.hero{background:linear-gradient(120deg,#101828,#27306B 58%,#4F46E5);color:#fff;padding:22px 26px;border-radius:18px;margin-bottom:14px;box-shadow:0 8px 24px rgba(16,24,40,.12)}
.eyebrow{font-size:11px;letter-spacing:.13em;font-weight:800;opacity:.72}.hero-title{font-size:29px;font-weight:900;letter-spacing:-.03em}.hero-sub{font-size:14px;opacity:.82;margin-top:5px}
.card{background:#fff;border:1px solid #E7EAF0;border-radius:16px;padding:18px 20px;box-shadow:0 2px 8px rgba(16,24,40,.04);height:100%}
.card-title{font-size:12px;font-weight:900;color:#475467;letter-spacing:.07em;margin-bottom:11px}.action{background:#EEF2FF;border:1px solid #C7D2FE;border-radius:14px;padding:15px 17px}.action-label{font-size:11px;font-weight:900;color:#4338CA}.action-value{font-size:24px;font-weight:900;color:#312E81;margin-top:2px}.action-code{font-size:11px;color:#6366F1;margin-top:2px}
.stage-wrap{display:grid;grid-template-columns:repeat(6,1fr);gap:7px}.stage{padding:10px 6px;border:1px solid #E7EAF0;border-radius:10px;text-align:center;font-size:12px;font-weight:800;color:#667085;background:#F8FAFC}.stage.done{background:#ECFDF3;color:#067647;border-color:#ABEFC6}.stage.current{background:#EEF2FF;color:#4338CA;border-color:#A5B4FC}
.fact-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.fact{background:#fff;border:1px solid #E7EAF0;border-radius:12px;padding:12px}.fact-k{font-size:11px;color:#667085;font-weight:700}.fact-v{font-size:14px;color:#172033;font-weight:900;margin-top:3px}
.ev{border:1px solid #E7EAF0;border-radius:10px;padding:9px 11px;margin-bottom:7px;background:#FCFCFD}.ev-name{font-size:13px;color:#172033;font-weight:800}.pill{display:inline-block;border-radius:999px;padding:4px 8px;font-size:11px;font-weight:900;margin-top:4px}.yes{background:#ECFDF3;color:#067647}.no{background:#F2F4F7;color:#475467}.warn{background:#FFFAEB;color:#B54708}
.rule{border-left:4px solid #F79009;background:#FFFAEB;padding:9px 11px;border-radius:8px;margin:7px 0;color:#7A2E0E;font-size:12px}.guide{display:grid;grid-template-columns:125px 1fr;border-bottom:1px solid #EAECF0;padding:9px 0;font-size:13px}.guide:last-child{border-bottom:none}.gk{font-weight:800;color:#667085}.gv{font-weight:700;color:#172033}.note{font-size:11px;color:#667085}.source{font-size:12px;color:#475467;background:#F8FAFC;padding:8px 10px;border-radius:8px;margin-bottom:5px}
</style>
""",
    unsafe_allow_html=True,
)

ACTIONS = ["CHECK_DOCUMENT", "ASK_SUPPLIER", "CHECK_SUPPLIER_READY", "SEND_NEGOTIATION", "WAIT_REPLY", "PREPARE_APPROVAL", "BLOCK", "COMPLETE"]
ACTION_KO = {
    "CHECK_DOCUMENT": "서류 추가 확인",
    "ASK_SUPPLIER": "업체 단독수행 근거 확인",
    "CHECK_SUPPLIER_READY": "공급사 MDVAN·수수료 확인",
    "SEND_NEGOTIATION": "수의시담 발송 준비",
    "WAIT_REPLY": "업체 회신 대기",
    "PREPARE_APPROVAL": "구매결재 작성 준비",
    "BLOCK": "진행 보류 / 확인 필요",
    "COMPLETE": "Case 완료",
}
STAGES = ["기안검토", "근거확인", "공급사확인", "수의시담", "구매결재", "계약"]


class TextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data and data.strip():
            self.parts.append(data.strip())


@dataclass
class Signals:
    purchase_doc: bool = False
    quote: bool = False
    exclusive_reason: bool = False
    mdvan_ready: bool = False
    fee_ready: bool = False
    quotation_ready: bool = False
    final_quote: bool = False
    prior_price_same: bool = False


@dataclass
class Facts:
    request_no: str = "미확인"
    item_type: str = "미확인"
    supplier: str = "미확인"
    item_name: str = "미확인"
    amount: str = "미확인"
    contract_period: str = "미확인"
    title: str = "미확인"


@dataclass
class Decision:
    state_code: str
    state_ko: str
    stage_idx: int
    next_action: str
    reason: str
    missing: List[str]
    rules: List[str]


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def has(text: str, words: List[str]) -> bool:
    low = text.lower()
    return any(w.lower() in low for w in words)


def html_to_text(raw: bytes) -> str:
    decoded = raw.decode("utf-8", errors="ignore")
    parser = TextHTMLParser()
    parser.feed(decoded)
    return "\n".join(parser.parts)


def bytes_to_text(name: str, raw: bytes) -> str:
    suffix = Path(name).suffix.lower()
    try:
        if suffix == ".pdf" and PdfReader is not None:
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((p.extract_text() or "") for p in reader.pages[:50])
        if suffix in {".html", ".htm"}:
            return html_to_text(raw)
        if suffix == ".docx" and Document is not None:
            doc = Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)
        if suffix in {".xlsx", ".xls"}:
            xls = pd.ExcelFile(io.BytesIO(raw))
            chunks = []
            for sheet in xls.sheet_names[:8]:
                df = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=250)
                chunks.append(df.fillna("").astype(str).to_csv(index=False, header=False))
            return "\n".join(chunks)
        if suffix in {".txt", ".md", ".csv"}:
            return raw.decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"[파일 읽기 오류: {name}] {exc}"
    return ""


def extract_uploaded(uploaded_files) -> Tuple[List[str], str]:
    names, chunks = [], []
    for uploaded in uploaded_files or []:
        name = uploaded.name
        raw = uploaded.getvalue()
        if Path(name).suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            continue
                        inner = info.filename
                        inner_raw = zf.read(info)
                        text = bytes_to_text(inner, inner_raw)
                        if text:
                            names.append(inner)
                            chunks.append(f"\n[FILE:{inner}]\n{text}")
            except Exception as exc:
                chunks.append(f"[ZIP 읽기 오류: {name}] {exc}")
        else:
            text = bytes_to_text(name, raw)
            names.append(name)
            chunks.append(f"\n[FILE:{name}]\n{text}")
    return names, "\n".join(chunks)


def first_match(text: str, patterns: List[str], default="미확인") -> str:
    for p in patterns:
        m = re.search(p, text, flags=re.I | re.S)
        if m:
            return norm(m.group(1))
    return default


def extract_facts(text: str) -> Facts:
    t = norm(text)
    request_no = first_match(t, [
        r"기안일자\s*[0-9]{4}\.[0-9]{2}\.[0-9]{2}\s*/\s*([0-9]{7,10})",
        r"요청번호.*?/\s*([0-9]{7,10})\s*기\s*안",
    ])
    item_type = first_match(t, [r"품목유형\s*([A-Za-z가-힣]+)"])
    supplier = first_match(t, [
        r"대상업체\s*[:：]?\s*((?:\(주\))?[^0-9]{2,30}?)(?=\s*[0-9]\.|\s*용도)",
        r"제조사명.*?((?:\(주\))?아이비리더스)",
    ])
    item_name = first_match(t, [r"(GRID\(IBSHEET\)\s*유지보수)", r"제품명\s*(IB\s*Sheet\s*8)"])
    amount = first_match(t, [
        r"금액\(VAT 포함\)\s*[:：]?\s*연간\s*([0-9,]+원)",
        r"견\s*적\s*금\s*액\s*[:：]?\s*([0-9,]+\s*원)",
        r"예상구입금액 합계.*?([0-9,]+)",
    ])
    start = first_match(t, [
        r"계약기간 시작일\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"유지보수 기간\s*[:：]?\s*([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일)",
    ])
    end = first_match(t, [
        r"계약기간 종료일\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"~\s*([0-9]{4}년\s*[0-9]{1,2}월\s*[0-9]{1,2}일)\s*\(12개월\)",
    ])
    period = f"{start} ~ {end}" if start != "미확인" or end != "미확인" else "미확인"
    title = first_match(t, [r"제\s*목\s*(MDVan.*?연장계약을 체결 건)(?=\s*계약주체)"])
    return Facts(request_no, item_type, supplier, item_name, amount, period, title)


def infer_signals(names: List[str], text: str) -> Signals:
    src = norm(" ".join(names) + " " + text)
    return Signals(
        purchase_doc=has(src, ["구매요청기안", "구매기안", "구매요청", "구매의뢰"]),
        quote=has(src, ["견적서", "견 적 금 액", "quotation"]),
        exclusive_reason=has(src, ["당사만 수행", "해당 업체만", "해당업체만", "단독 수행", "단독수행", "타사 수행 불가", "본인들밖에", "유일 공급"]),
        mdvan_ready=has(src, ["mdvan 가입 가능", "mdvan가입 가능", "공급사 등록 가능", "가입가능"]),
        fee_ready=has(src, ["수수료 수용", "수수료 허용", "수수료 적용 가능", "수수료 가능"]),
        quotation_ready=has(src, ["견적 제출 가능", "견적제출 가능", "견적 진행 가능", "견적 가능"]),
        final_quote=has(src, ["최종 견적", "최종견적", "final quotation", "final quote"]),
        prior_price_same=has(src, ["작년 금액과 동일", "종전과 동일", "전년 금액과 동일", "전년도 금액과 동일"]),
    )


def demo_signals(step: int) -> Signals:
    s = Signals(purchase_doc=True, quote=True, prior_price_same=True)
    if step >= 2:
        s.exclusive_reason = True
    if step >= 3:
        s.mdvan_ready = s.fee_ready = s.quotation_ready = True
    if step >= 4:
        s.final_quote = True
    return s


def decide(s: Signals, purchase_type: str) -> Decision:
    rules = [
        "AI가 구매기안의 구매유형을 임의로 변경하지 않습니다.",
        "MDVAN 실제 발송·결재상신은 담당자가 최종 확인합니다.",
    ]
    if purchase_type == "일반":
        rules.append("일반구매 기안은 사후 단수·긴급 근거만으로 AI가 구매유형을 변경하지 않습니다.")
    if not (s.purchase_doc or s.quote):
        return Decision("DOCUMENT_REQUIRED", "기초 서류 확인 필요", 0, "CHECK_DOCUMENT", "판단에 필요한 구매요청 또는 견적 근거가 없습니다.", ["구매요청 자료", "견적자료"], rules)
    if not s.exclusive_reason:
        return Decision("SUPPLIER_EVIDENCE_REQUIRED", "단일 공급사 근거 확인 필요", 1, "ASK_SUPPLIER", "구매기안과 기존 견적은 확인되지만 특정 공급사만 진행해야 하는 근거는 문서에서 확인되지 않습니다. 업체에 단독 수행 가능 여부와 근거를 확인하는 것이 다음 행동입니다.", ["해당 업체만 수행 가능한 사유", "가능하면 업체 서면 근거", "MDVAN 가입 및 수수료 수용 가능 여부"], rules)
    if not (s.mdvan_ready and s.fee_ready and s.quotation_ready):
        missing = []
        if not s.mdvan_ready:
            missing.append("MDVAN 가입/등록 가능 여부")
        if not s.fee_ready:
            missing.append("수수료 적용 수용 여부")
        if not s.quotation_ready:
            missing.append("견적 제출 가능 여부/시점")
        return Decision("SUPPLIER_READY_CHECK", "공급사 진행조건 확인", 2, "CHECK_SUPPLIER_READY", "단일 공급사 근거가 확보되었습니다. 수의시담 전에 공급사의 MDVAN 이용, 수수료 수용, 견적 제출 가능 여부를 확인해야 합니다.", missing, rules)
    if not s.final_quote:
        return Decision("READY_FOR_NEGOTIATION", "수의시담 진행 가능", 3, "SEND_NEGOTIATION", "단일 공급사 근거와 공급사 진행조건이 확인되어 수의시담 발송 준비가 가능합니다.", [], rules)
    return Decision("NEGOTIATION_RESULT_RECEIVED", "최종 견적 회신 확인", 4, "PREPARE_APPROVAL", "최종 견적이 확인되어 가격비교와 구매결재 작성 단계로 이동할 수 있습니다.", [], rules)


def mdvan_guide(action: str, supplier: str, prior_same: bool) -> List[Tuple[str, str]]:
    supplier = supplier if supplier and supplier != "미확인" else "해당 공급사"
    if action == "ASK_SUPPLIER":
        return [
            ("현재 MDVAN", "아직 수의시담 발송하지 않음"),
            ("업체 확인", f"{supplier}만 수행 가능한 이유 및 서면 근거 요청"),
            ("동시 확인", "MDVAN 가입/등록, 수수료 수용, 견적 제출 가능 여부"),
            ("가격검토 방향", "기안에 '작년 금액과 동일'이 있어 종전가격 비교 자료로 활용 가능" if prior_same else "종전가격 등 가격검증 근거 확인"),
        ]
    if action == "CHECK_SUPPLIER_READY":
        return [
            ("현재 MDVAN", "수의시담 발송 전 사전 확인"),
            ("공급사", supplier),
            ("확인 1", "MDVAN 가입/등록 가능 여부"),
            ("확인 2", "IT 수수료 적용 수용 여부"),
            ("확인 3", "견적 제출 가능 시점"),
        ]
    if action == "SEND_NEGOTIATION":
        return [
            ("메뉴", "MDVAN > 수의시담/가격조사 발송 화면"),
            ("공급사", supplier),
            ("첨부", "사양/요청자료 및 견적에 필요한 문서"),
            ("이지메모", "해당 구매 건 관련 수의시담 요청드립니다. 첨부자료 확인 후 견적 제출 부탁드립니다."),
            ("실행", "공급사·첨부·수수료 조건 확인 후 담당자가 발송"),
        ]
    if action == "PREPARE_APPROVAL":
        return [
            ("다음 화면", "구매결재 작성"),
            ("가격비교", "종전가격과 최종견적 비교" if prior_same else "가용한 가격근거와 최종견적 비교"),
            ("작성", "9. 가격조사기준 / 10. 특이사항 정리"),
            ("실행", "금액·수수료·계약방법 확인 후 담당자가 상신"),
        ]
    return [("현재 작업", "추가 서류 확인 후 다시 분석")]


def render_stages(idx: int):
    html = '<div class="stage-wrap">'
    for i, s in enumerate(STAGES):
        cls = "stage done" if i < idx else ("stage current" if i == idx else "stage")
        html += f'<div class="{cls}">{s}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def llm_select(case_id: str, purchase_type: str, facts: Facts, signals: Signals, base: Decision, text: str, api_key: str, model: str) -> Optional[dict]:
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = f"""당신은 의료 GPO 구매 Case의 Next Action Selector다.
현재 Case를 완료하기 위한 다음 행동 하나를 허용 Action에서 선택한다.
허용 Action: {ACTIONS}
구매유형과 회사 Guardrail은 절대 임의 변경하지 않는다. 실제 MDVAN 클릭/발송을 했다고 말하지 않는다.
Case={case_id}\n구매유형={purchase_type}\nFacts={asdict(facts)}\nSignals={asdict(signals)}\nRuleEngine={asdict(base)}\nEvidence={norm(text)[:16000]}
JSON만 반환: {{"next_action":"...","reason":"한국어 2~3문장","missing":["..."],"risk_note":"..."}}"""
        r = client.responses.create(model=model, store=False, input=prompt)
        m = re.search(r"\{.*\}", r.output_text, flags=re.S)
        if not m:
            return None
        out = json.loads(m.group(0))
        return out if out.get("next_action") in ACTIONS else None
    except Exception:
        return None


st.markdown('<div class="hero"><div class="eyebrow">HUMAN-IN-THE-LOOP PROCUREMENT AGENT · POC</div><div class="hero-title">구매 Case AI Agent</div><div class="hero-sub">실제 구매서류를 읽고 현재 State → Next Action → MDVAN 처리 가이드를 연결합니다.</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Case 설정")
    case_id = st.text_input("Case 번호", "KDWEZ202600338", help="실제 문서에 Case 번호가 없어도 됩니다.")
    purchase_type = st.selectbox("구매기안 유형", ["일반", "단수", "긴급"], index=0)
    st.markdown("---")
    demo_mode = st.toggle("발표 데모 모드", True)
    step = st.radio("시연 단계", ["1. 실제 최초 서류", "2. 단독 수행 근거 확보", "3. 공급사 진행조건 확인", "4. 최종 견적 회신"], index=0) if demo_mode else None
    st.markdown("---")
    uploads = st.file_uploader("실제 Case 서류 업로드", type=["zip", "pdf", "html", "htm", "docx", "xlsx", "xls", "txt", "md", "csv"], accept_multiple_files=True, help="KDWEZ202600338.zip을 그대로 올릴 수 있습니다.")
    st.markdown("---")
    use_llm = st.toggle("LLM Next Action Selector", False)
    api_key = st.text_input("OPENAI_API_KEY", type="password", value=os.getenv("OPENAI_API_KEY", "")) if use_llm else ""
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-5")) if use_llm else "gpt-5"
    analyze = st.button("AI Agent 분석 시작", type="primary", use_container_width=True)

names, text = extract_uploaded(uploads)
facts = extract_facts(text) if text else Facts()
real_signals = infer_signals(names, text) if text else Signals()

if demo_mode:
    signals = demo_signals(int(step.split(".")[0]))
    if text:
        signals.purchase_doc = real_signals.purchase_doc or signals.purchase_doc
        signals.quote = real_signals.quote or signals.quote
        signals.prior_price_same = real_signals.prior_price_same or signals.prior_price_same
else:
    signals = real_signals

base = decide(signals, purchase_type)
llm = llm_select(case_id, purchase_type, facts, signals, base, text, api_key, model) if analyze and use_llm else None
action = llm.get("next_action", base.next_action) if llm else base.next_action
reason = llm.get("reason", base.reason) if llm else base.reason
missing = llm.get("missing", base.missing) if llm else base.missing

st.markdown("### Case 기본정보")
fact_items = [
    ("Case 번호", case_id or "미입력"),
    ("요청번호", facts.request_no),
    ("품목유형", facts.item_type),
    ("공급사", facts.supplier),
    ("예상/견적금액", facts.amount),
    ("계약기간", facts.contract_period),
]
html = '<div class="fact-grid">' + ''.join(f'<div class="fact"><div class="fact-k">{k}</div><div class="fact-v">{v}</div></div>' for k, v in fact_items) + '</div>'
st.markdown(html, unsafe_allow_html=True)
if facts.title != "미확인":
    st.caption(f"문서 제목: {facts.title}")

st.markdown("### 업무 진행 상태")
render_stages(base.stage_idx)

left, right = st.columns([1.3, 1], gap="large")
with left:
    st.markdown(f'<div class="card"><div class="card-title">AGENT DECISION</div><div class="action"><div class="action-label">NEXT ACTION</div><div class="action-value">{ACTION_KO.get(action, action)}</div><div class="action-code">{action}</div></div><div style="font-size:13px;font-weight:900;margin-top:14px">판단 이유</div><div style="font-size:14px;color:#475467;line-height:1.65;margin-top:5px">{reason}</div></div>', unsafe_allow_html=True)
    st.markdown("#### MDVAN / 담당자 처리 가이드")
    g = '<div class="card">'
    for k, v in mdvan_guide(action, facts.supplier, signals.prior_price_same):
        g += f'<div class="guide"><div class="gk">{k}</div><div class="gv">{v}</div></div>'
    st.markdown(g + '</div>', unsafe_allow_html=True)
with right:
    st.markdown("#### Evidence Check")
    evidence = [
        ("구매기안/요청자료", signals.purchase_doc),
        ("기존 견적", signals.quote),
        ("단일 공급사 근거", signals.exclusive_reason),
        ("MDVAN 가입/등록", signals.mdvan_ready),
        ("수수료 수용", signals.fee_ready),
        ("견적 제출 가능", signals.quotation_ready),
        ("최종 견적", signals.final_quote),
        ("종전가격 동일 근거", signals.prior_price_same),
    ]
    for n, ok in evidence:
        cls = "yes" if ok else "no"
        label = "확인" if ok else "미확인"
        st.markdown(f'<div class="ev"><div class="ev-name">{n}</div><span class="pill {cls}">{label}</span></div>', unsafe_allow_html=True)
    if missing:
        st.markdown("#### 추가 확인 필요")
        for m in missing:
            st.markdown(f"- **{m}**")
    st.markdown("#### Guardrail")
    for r in base.rules:
        st.markdown(f'<div class="rule">{r}</div>', unsafe_allow_html=True)
    st.markdown('<span class="pill warn">Human approval required</span>', unsafe_allow_html=True)

if names:
    st.markdown("### 읽은 실제 파일")
    for n in names:
        st.markdown(f'<div class="source">{n}</div>', unsafe_allow_html=True)

with st.expander("기술 로그 / 추출 텍스트", False):
    st.json({"case_id": case_id, "facts": asdict(facts), "signals": asdict(signals), "state": base.state_code, "rule_action": base.next_action, "effective_action": action, "llm_used": bool(llm)})
    if text:
        st.text_area("문서 추출 텍스트", text[:15000], height=260)

st.markdown('<div class="note">PoC 범위: 실제 문서/ZIP 관찰 → State 생성 → Rule Guardrail → Next Action 선택 → MDVAN 처리 안내. MDVAN 자동 클릭·발송·계약상신은 포함하지 않습니다.</div>', unsafe_allow_html=True)
