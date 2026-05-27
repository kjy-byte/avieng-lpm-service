import streamlit as st
import requests
import base64
import csv
from io import StringIO

from datetime import datetime, timedelta

# =====================================================
# 1. 페이지 설정 및 상태 초기화
# =====================================================
if "maker_list" not in st.session_state:
    st.session_state.maker_list = [""]

if "requester_map" not in st.session_state:
    st.session_state.requester_map = {}

st.set_page_config(page_title="장비 점검 관리 프로그램", layout="wide")

if "save_success" not in st.session_state: st.session_state.save_success = False
if "reset_required" not in st.session_state: st.session_state.reset_required = False
if "upload_key" not in st.session_state: st.session_state.upload_key = 0
# [오류 방지 핵심] 위젯 렌더링 전, 초기화 플래그를 확인하여 값 비우기
if st.session_state.reset_required:
    for key in [
        "customer",
        "fab",
        "process",
        "manager",
        "company",
        "company_manager",  # 추가
        "requester_selected",
        "writer",
        "unit_name",
        "po_code"
    ]:
        st.session_state[key] = ""

    for i in range(1, 5):
        for k in ["code", "lp", "mfg", "date", "fw", "err", "work"]:
            st.session_state[f"{k}_{i}"] = ""

    # 시간 초기화 (현재 시간으로 설정)
    now = datetime.now().time()
    for p in ["reg", "over"]:
        for i in range(1, 3):
            st.session_state[f"{p}_w{i}"] = ""
            st.session_state[f"{p}_t{i}"] = ""
            # 추가
            st.session_state[f"{p}_travel_apply{i}"] = None
            st.session_state[f"{p}_r{i}"] = 0.0
            st.session_state[f"{p}_s{i}"] = now
            st.session_state[f"{p}_e{i}"] = now

    st.session_state["work_type"] = "점검"
    st.session_state["warranty"] = None
    st.session_state["payment"] = None
    # 업로드 파일 초기화용 key 변경
    st.session_state.upload_key += 1
    st.session_state.reset_required = False

if st.session_state.save_success:
    st.toast("구글시트 저장 완료!", icon="✅")
    st.session_state.save_success = False


# =====================================================
# 2. 함수 정의
# =====================================================
@st.cache_data(ttl=300)
def load_maker_list():

    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTUfTySn8scuRIz5U0ONICRjSEOn_0PtDrHIx1l8sAykH_hkYYbf4bR83-izE-NFt6wDIkQ8n1RQ_qM/pub?output=csv"

    try:
        response = requests.get(url)
        response.raise_for_status()

        # 한글 깨짐 방지
        csv_text = response.content.decode("utf-8-sig")

        csv_data = StringIO(csv_text)
        reader = csv.reader(csv_data)
        rows = list(reader)

        maker_list = []

        for row in rows[1:]:
            if len(row) > 0 and row[0].strip():
                maker_list.append(row[0].strip())

        return [""] + maker_list

    except Exception as e:
        st.error(f"장비사 목록을 불러오지 못했습니다: {e}")
        return [""]


@st.cache_data(ttl=300)
def load_requester_list(company_name):
    selected_company = company_name.strip()

    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRjlxwiE9ku7E9oX2t8BRtAraX_Iv9FJVFDfpiLBzBFiMqhtGOeIZ5-aAZkgV7PdSx5Ap6Bdio_wHqg/pub?output=csv"

    try:
        response = requests.get(url)
        response.raise_for_status()

        csv_text = response.content.decode("utf-8-sig")
        csv_data = StringIO(csv_text)
        reader = csv.reader(csv_data)
        rows = list(reader)

        requester_map = {}

        for row in rows[1:]:
            if len(row) >= 7:
                sheet_company = row[0].strip()
                name = row[3].strip()
                phone = row[4].strip()
                email = row[5].strip()
                cc_mail = row[6].strip()

                if sheet_company.replace(" ", "").upper() == selected_company.replace(" ", "").upper() and name:
                    display = f"{name} / {phone}"

                    requester_map[display] = {
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "cc_mail": cc_mail
                    }

        return requester_map

    except Exception as e:
        st.error(f"요청자 목록을 불러오지 못했습니다: {e}")
        return {}

def calc_work_hours(start_time, end_time):
    if not start_time or not end_time: return 0.0
    try:
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)
        if end_dt < start_dt: end_dt += timedelta(days=1)
        return round((end_dt - start_dt).total_seconds() / 3600, 1)
    except:
        return 0.0


def work_card(title, prefix, idx, bg_color, expanded=False):

    with st.expander(title, expanded=expanded):

        st.markdown(
            f"""
            <div style="
                background:{bg_color};
                color:white;
                padding:4px 12px;
                border-radius:15px;
                width:fit-content;
                font-size:14px;
                font-weight:600;
                margin-bottom:15px;">
                {title}
            </div>
            """,
            unsafe_allow_html=True
        )

        # =========================
        # 한줄 배치
        # 작업자 | 이동시간적용 | 작업 시작시간 | 작업 종료시간 | Hourly Rate | Travel
        # =========================
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.6, 1.3, 1.3, 1, 1.2])

        # 작업자
        with c1:
            st.text_input(
                "작업자",
                key=f"{prefix}_w{idx}"
            )

        # 이동시간적용
        with c2:
            left_space, radio_col, right_space = st.columns([1, 2, 1])

            with radio_col:
                st.radio(
                    "이동시간적용",
                    ["적용", "미적용"],
                    horizontal=True,
                    index=None,
                    key=f"{prefix}_travel_apply{idx}"
                )

        # 작업 시작시간
        with c3:
            st.time_input(
                "작업 시작시간",
                key=f"{prefix}_s{idx}"
            )

        # 작업 종료시간
        with c4:
            st.time_input(
                "작업 종료시간",
                key=f"{prefix}_e{idx}"
            )

        # Travel
        with c5:
            st.text_input(
                "Travel",
                key=f"{prefix}_t{idx}"
            )

        # Hourly Rate
        with c6:
            st.text_input(
                "Hourly Rate",
                key=f"{prefix}_r{idx}"
            )


# =====================================================
# 3. 메인 화면 구성
# =====================================================
st.title("장비 점검 관리 프로그램")
st.header("1. 기본 정보")

# =========================
# 장비사 목록 버튼
# =========================
if st.button(
    "장비사 목록 불러오기",
    key="load_maker_btn"
):
    load_maker_list.clear()
    st.session_state.maker_list = load_maker_list()
    st.rerun()

# =========================
# 1줄: 점검일 / FAB / 공정 / 담당자
# =========================
c1, c2, c3, c4, c5 = st.columns(5)

inspect_date = c1.date_input("점검일")

customer = c2.selectbox(
    "고객사",
    [
        "",
        "삼성",
        "하이닉스",
        "그 외"
    ],
    key="customer"
)

fab = c3.text_input(
    "FAB NAME",
    key="fab"
)

process = c4.selectbox(
    "공정",
    [
        "",
        "CMP",
        "CVD",
        "CLEAN",
        "DEPO",
        "DIFF",
        "ETCH",
        "IMP",
        "METAL",
        "POLY",
        "PHOTO",
        "PVD",
        "RTP",
        "SABRE",
        "SABRE 3D",
        "SORTER",
        "계측",
        "Others"
    ],
    key="process"
)

manager = c5.text_input(
    "현업 담당자",
    key="manager"
)

# -----------------------------
# 2줄: 현업 담당자 / 장비사 / 호기명
# -----------------------------


# =========================
# 장비사
# =========================
# -----------------------------
# 2줄: 장비사 / 버튼 / 호기명 / 장비사 담당자 / 요청자 선택
# -----------------------------
c5, c6, c7, c8, c9 = st.columns([2, 1.6, 2, 2, 2.5])

with c5:
    company = st.selectbox(
        "장비사",
        st.session_state.maker_list,
        key="company"
    )

with c6:
    st.markdown(
        """
        <div style="height: 27px;"></div>
        """,
        unsafe_allow_html=True
    )
    if st.button(
        "장비사 요청자 메일주소 가져오기",
        key="load_requester_btn"
    ):
        selected_company = st.session_state.get("company", "")

        if not selected_company:
            st.warning("장비사를 먼저 선택해주세요.")
        else:
            load_requester_list.clear()
            st.session_state.requester_map = load_requester_list(selected_company)
            st.session_state.requester_selected = ""

            if not st.session_state.requester_map:
                st.warning(f"{selected_company} 요청자 목록이 없습니다.")
            else:
                st.success(f"{selected_company} 요청자 목록을 불러왔습니다.")

            st.rerun()

with c7:
    unit_name = st.text_input(
        "호기명",
        key="unit_name"
    )

with c8:
    company_manager = st.text_input(
        "장비사 담당자",
        key="company_manager"
    )

requester_options = [""] + list(st.session_state.requester_map.keys())

with c9:
    requester_selected = st.selectbox(
        "장비사 요청자 메일주소 선택",
        requester_options,
        key="requester_selected"
    )

# -----------------------------
# 다음 줄: AVIENG 작업자
# -----------------------------
c10, _ = st.columns([2, 3])

with c10:
    writer = st.selectbox(
        "AVIENG 작업자",
        [
            "",
            "이영민",
            "진경호",
            "김인덕",
            "김석정",
            "김영민",
            "남경완",
            "New1",
            "New2",
            "New3",
            "New4"
        ],
        key="writer"
    )


st.header("첨부 파일")
uploaded_file = st.file_uploader(
    "서비스레포트 업로드",
    type=["pdf", "jpg", "jpeg", "png"],
    key=f"uploaded_file_{st.session_state.upload_key}"
)
st.header("2. 작업 정보")

c1, c2 = st.columns(2)
po_code = c1.text_input("PO / AS CODE / SVO", key="po_code")
work_type = c2.selectbox("작업구분", ["점검", "부품교체", "개조", "설치", "파라메터", "펌웨어", "기타"], key="work_type")

st.header("3. 장비 정보")

col_eq, _ = st.columns([1, 4])
with col_eq:
    equipment_count = st.selectbox(
        "입력할 장비이력 수량 선택",
        [1, 2, 3, 4],
        index=0
    )

for i in range(1, equipment_count + 1):
    with st.expander(f"장비 {i} 상세 정보", expanded=(i == 1)):

        c0, c00 = st.columns(2)
        c0.text_input(f"장비코드_{i}", key=f"code_{i}")
        c00.text_input(f"LP타입_{i}", key=f"lp_{i}")

        c1, c2, c3 = st.columns(3)
        c1.text_input(f"MFGNO_{i}", key=f"mfg_{i}")
        c2.text_input(f"제조일자_{i}", key=f"date_{i}")
        c3.text_input(f"F/W_{i}", key=f"fw_{i}")

        st.text_area(f"Error현상_{i}", key=f"err_{i}")
        st.text_area(f"작업내용_{i}", key=f"work_{i}")

st.header("4. 작업 시간 및 비용")
work_card("Regular 작업 1", "reg", 1, "#1E3A5F", expanded=True)

use_reg2 = st.checkbox("Regular 작업 2 추가")
use_over1 = st.checkbox("Overtime 작업 1 추가")
use_over2 = st.checkbox("Overtime 작업 2 추가")

if use_reg2:
    work_card("Regular 작업 2", "reg", 2, "#1E3A5F", expanded=False)

if use_over1:
    work_card("Overtime 작업 1", "over", 1, "#F57C00", expanded=False)

if use_over2:
    work_card("Overtime 작업 2", "over", 2, "#F57C00", expanded=False)

st.header("5. 보증 및 비용 구분")

c1, c2 = st.columns(2)
warranty = c1.radio("보증기간",["보증 내", "보증 외"],horizontal=True,index=None,key="warranty")
payment = c2.radio("비용지불",["유상", "무상"],horizontal=True,index=None,key="payment")

# =====================================================
# 4. 저장 버튼 로직
# =====================================================
if st.button("저장", type="primary"):
    # 작업자 선택 체크
    if not st.session_state.get("writer"):
        st.warning("작업자를 선택해주세요.")
        st.stop()

    # 보증기간 체크
    if not st.session_state.get("warranty"):
        st.warning("보증기간을 선택해주세요.")
        st.stop()

    # 비용지불 체크
    if not st.session_state.get("payment"):
        st.warning("비용지불 여부를 선택해주세요.")
        st.stop()

    # 고객사 체크
    if not st.session_state.get("customer"):
        st.warning("고객사를 선택해주세요.")
        st.stop()

    # 공정 체크
    if not st.session_state.get("process"):
        st.warning("공정을 선택해주세요.")
        st.stop()

    # 장비사 요청자 체크
    if not st.session_state.get("requester_selected"):
        st.warning("장비사 요청자를 선택해주세요.")
        st.stop()

    # 이동시간 적용 여부 체크
    # 작업자가 입력된 경우만 검사
    # =========================
    for p in ["reg", "over"]:
        for i in range(1, 3):
            # 작업자 입력 여부
            worker = st.session_state.get(f"{p}_w{i}")
            # 작업자가 있을 때만 검사
            if worker:
                if not st.session_state.get(f"{p}_travel_apply{i}"):
                    st.warning(f"{p.upper()} 작업 {i}의 이동시간 적용 여부를 선택해주세요.")
                    st.stop()

    # 업로드 파일 처리
    file_data = ""
    file_name = ""
    file_type = ""
    file_url = ""  # 저장 후 URL 받을 변수

    if uploaded_file is not None:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("10MB 이하 파일만 업로드 가능합니다.")
            st.stop()
        file_data = base64.b64encode(
            uploaded_file.read()
        ).decode("utf-8")
        file_name = uploaded_file.name
        file_type = uploaded_file.type

    with st.spinner("저장 중..."):
        # =======================
        # 작업시간 계산
        # =======================
        total = sum([calc_work_hours(st.session_state.get(f"{p}_s{i}"),
                                     st.session_state.get(f"{p}_e{i}")) *
                     st.session_state.get(f"{p}_r{i}", 0)
                     for p in ["reg", "over"] for i in range(1, 3)])

        # =======================
        # 기본 정보 + 장비 + 작업 데이터
        # =======================
        customer_value = st.session_state.get("customer", "")
        fab_value = st.session_state.get("fab", "")
        fab_data = f"{customer_value} / {fab_value}"

        requester_info = st.session_state.requester_map.get(
            st.session_state.get("requester_selected", ""),
            {}
        )
        requester_display = st.session_state.get("requester_selected", "")
        requester_email = requester_info.get("email", "")
        requester_cc_mail = requester_info.get("cc_mail", "")

        if requester_email and requester_cc_mail:
            requester_mail_data = f"{requester_email}\n{requester_cc_mail}"
        elif requester_email:
            requester_mail_data = requester_email
        else:
            requester_mail_data = requester_cc_mail

        data = {
            "inspect_date": str(inspect_date),
            "customer": st.session_state.get("customer", ""),
            "fab": fab_data,
            "process": st.session_state.get("process", ""),
            "manager": st.session_state.get("manager", ""),
            "company": st.session_state.get("company", ""),
            "company_manager": st.session_state.get("company_manager", ""),
            "unit_name": st.session_state.get("unit_name", ""),

            # 장비사 요청자 정보
            # 화면 표시: D열 / E열
            # DATA 전송: D/E/F/G열 각각 분리 전송
            "requester": requester_display,
            "requester_phone": requester_info.get("phone", ""),
            "requester_mail": requester_mail_data,
            "requester_cc_mail": requester_info.get("cc_mail", ""),

            "writer": st.session_state.get("writer", ""),
            "po_code": st.session_state.get("po_code", ""),
            "work_type": st.session_state.get("work_type", ""),

            # 추가
            "equipment_count": equipment_count,

            "total_amount": total,
            "warranty": st.session_state.get("warranty", ""),
            "payment": st.session_state.get("payment", "")
        }

        for i in range(1, 5):
            for k in ["code", "lp", "mfg", "date", "fw", "err", "work"]:
                data[f"eq{i}_{k}"] = st.session_state.get(f"{k}_{i}", "")

        mapping = [(1, "reg", 1), (2, "reg", 2), (3, "over", 1), (4, "over", 2)]
        for idx, prefix, sub_idx in mapping:
            data[f"div{idx}"] = prefix
            data[f"worker{idx}"] = st.session_state.get(f"{prefix}_w{sub_idx}", "")
            data[f"start{idx}"] = str(st.session_state.get(f"{prefix}_s{sub_idx}", ""))
            data[f"end{idx}"] = str(st.session_state.get(f"{prefix}_e{sub_idx}", ""))
            work_hr = calc_work_hours(st.session_state.get(f"{prefix}_s{sub_idx}"),
                                      st.session_state.get(f"{prefix}_e{sub_idx}"))
            data[f"hour{idx}"] = float(work_hr)
            data[f"travel{idx}"] = st.session_state.get(f"{prefix}_t{sub_idx}", "")
            data[f"travel_apply{idx}"] = st.session_state.get(f"{prefix}_travel_apply{sub_idx}", "")
            data[f"rate{idx}"] = float(st.session_state.get(f"{prefix}_r{sub_idx}", 0.0))

        # =======================
        # Google Apps Script 전송
        # =======================
        # 첨부파일 정보도 마지막에 추가
        data["file_name"] = file_name
        data["file_type"] = file_type
        data["file_data"] = file_data

        url = "https://script.google.com/macros/s/AKfycby2ocIW3lpLnUMo0EZ9hYhp__yGJmMG8wfYixPni2abIbSdWHkq0MoJhoaPyYlxlcWxAQ/exec"
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                st.session_state.reset_required = True
                st.session_state.save_success = True
                st.rerun()
            else:
                st.error(f"저장 실패: {response.text}")
        except Exception as e:
            st.error(f"오류: {e}")