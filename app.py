import streamlit as st
import requests
import base64

from datetime import datetime, timedelta

# =====================================================
# 1. 페이지 설정 및 상태 초기화
# =====================================================
st.set_page_config(page_title="장비 점검 관리 프로그램", layout="wide")

if "save_success" not in st.session_state: st.session_state.save_success = False
if "reset_required" not in st.session_state: st.session_state.reset_required = False
if "upload_key" not in st.session_state: st.session_state.upload_key = 0
# [오류 방지 핵심] 위젯 렌더링 전, 초기화 플래그를 확인하여 값 비우기
if st.session_state.reset_required:
    for key in [
        "fab",
        "process",
        "manager",
        "company",
        "requester",
        "writer",
        "service_order",
        "requester_mail",
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

        # 좌우 컬럼 생성
        left, right = st.columns(2)

        # =========================
        # 왼쪽 영역
        # =========================
        with left:

            st.text_input(
                "작업자",
                key=f"{prefix}_w{idx}"
            )

            st.time_input(
                "작업 시작시간",
                key=f"{prefix}_s{idx}"
            )

            st.time_input(
                "작업 종료시간",
                key=f"{prefix}_e{idx}"
            )

        # =========================
        # 오른쪽 영역
        # =========================
        with right:
            st.radio(
                "이동시간적용",
                ["적용", "미적용"],
                horizontal=True,
                index=None,
                key=f"{prefix}_travel_apply{idx}"
            )

            st.number_input(
                "Hourly Rate",
                min_value=0.0,
                step=1.0,
                key=f"{prefix}_r{idx}"
            )

            st.text_input(
                "Travel",
                key=f"{prefix}_t{idx}"
            )


# =====================================================
# 3. 메인 화면 구성
# =====================================================
st.title("장비 점검 관리 프로그램")
st.header("1. 기본 정보")

# -----------------------------
# 1줄: 점검일 / FAB / 공정
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
inspect_date = c1.date_input("점검일")
fab = c2.text_input("FAB", key="fab")
process = c3.text_input("공정", key="process")
manager = c4.text_input("현업 담당자", key="manager")
# -----------------------------
# 2줄: 현업 담당자 / 장비사 / 호기명
# -----------------------------
c5, c6, c7 = st.columns(3)
company = c5.text_input("장비사", key="company")
unit_name = c6.text_input("호기명", key="unit_name")
requester = c7.text_input("장비사 요청자", key="requester")

# -----------------------------
# 3줄: 장비사 요청자 / 작업자 / Service Order
# -----------------------------
c8, c9, c10 = st.columns(3)
writer = c8.selectbox(
    "작업자",
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
service_order = c9.text_input("Service Order", key="service_order")
requester_mail = c10.text_input("장비사 요청자 메일주소", key="requester_mail")

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

for i in range(1, 5):
    with st.expander(f"장비 {i} 상세 정보",expanded=(i == 1)):
        # =========================
        # 장비코드 / LP타입
        # =========================
        c0, c00 = st.columns(2)
        c0.text_input(f"장비코드_{i}",key=f"code_{i}")
        c00.text_input(f"LP타입_{i}",key=f"lp_{i}")

        # =========================
        # MFG / 제조일자 / FW
        # =========================
        c1, c2, c3 = st.columns(3)
        c1.text_input(f"MFGNO_{i}",key=f"mfg_{i}")
        c2.text_input(f"제조일자_{i}",key=f"date_{i}")
        c3.text_input(f"F/W_{i}",key=f"fw_{i}")
        st.text_area(f"Error현상_{i}",key=f"err_{i}")
        st.text_area(f"작업내용_{i}",key=f"work_{i}")

st.header("4. 작업 시간 및 비용")
work_card("Regular 작업 1", "reg", 1, "#1E3A5F", expanded=True)
work_card("Regular 작업 2", "reg", 2, "#1E3A5F", expanded=False)
work_card("Overtime 작업 1", "over", 1, "#F57C00", expanded=False)
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
        data = {
            "inspect_date": str(inspect_date),
            "fab": st.session_state.get("fab", ""),
            "process": st.session_state.get("process", ""),
            "manager": st.session_state.get("manager", ""),
            "company": st.session_state.get("company", ""),
            "unit_name": st.session_state.get("unit_name", ""),
            "requester": st.session_state.get("requester", ""),
            "writer": st.session_state.get("writer", ""),
            "service_order": st.session_state.get("service_order", ""),
            "requester_mail": st.session_state.get("requester_mail", ""),
            "po_code": st.session_state.get("po_code", ""),
            "work_type": st.session_state.get("work_type", ""),
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

        url = "https://script.google.com/macros/s/AKfycbyf-Gi_mQoDli4evaX_R2EwWNMAdWkneVdOCbjmm3Yk5pmF77sLQsnLMbvUJkMdPXSwKg/exec"
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