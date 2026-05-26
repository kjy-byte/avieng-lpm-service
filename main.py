# flet build apk 앱생성
# .\venv4\Scripts\flet build apk --compile-to-wasm
# .\venv4\Scripts\flet build apk --flutter-flags="--target-platform=android-arm64" (arm64만 빌드)
# flet build web 웹 배포
# flet build web --web-renderer html (다운로드 용량 감소 / 초기 로딩 빨라짐)
# flet build web --web-renderer html --no-web-splash
# =========================================================
# Google Apps Script URL
# =========================================================

import flet as ft
import requests  # ⭐️ 안드로이드 안정성을 위해 httpx 대신 requests로 교체

# =========================================================
# Google Apps Script URL
# =========================================================
url = "https://script.google.com/macros/s/AKfycbyY10GdKGlNTUbEynrWoHlA6T4OYW_x5XCamYVXsVSRSJY205V6AziKnBJRsZkghsCiDQ/exec"
SCRIPT_URL = url


def main(page: ft.Page):
    page.title = "장비 점검 관리 프로그램"
    page.window_maximized = True
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # =========================================================
    # 공통 함수 (클로저 및 토글 글자 변경 제어)
    # =========================================================
    def toggle_section(e, content_panel, btn):
        content_panel.visible = not content_panel.visible
        btn.content.controls[0].value = "[ 닫기 ]" if content_panel.visible else "[ 펼치기 ]"
        page.update()

    # =========================================================
    # 첫번째 메뉴
    # =========================================================
    inspect_date = ft.TextField(label="점검일")
    fab = ft.TextField(label="FAB")
    process = ft.TextField(label="공정")
    manager = ft.TextField(label="현업담당자")
    company = ft.TextField(label="장비사명")
    requester = ft.TextField(label="장비사요청자")
    writer = ft.TextField(label="작성자")

    first_menu = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("1. 기본 정보", size=24, weight=ft.FontWeight.BOLD),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(inspect_date, col={"md": 4}),
                            ft.Container(fab, col={"md": 4}),
                            ft.Container(process, col={"md": 4}),
                        ]
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(manager, col={"md": 4}),
                            ft.Container(company, col={"md": 4}),
                            ft.Container(requester, col={"md": 4}),
                        ]
                    ),
                    ft.ResponsiveRow(controls=[ft.Container(writer, col={"md": 4})]),
                ]
            )
        )
    )

    # =========================================================
    # 두번째 메뉴
    # =========================================================
    po_code = ft.TextField(label="PO / AS CODE / SVO")
    work_type = ft.Dropdown(
        label="작업구분",
        options=[
            ft.dropdown.Option("점검"),
            ft.dropdown.Option("부품교체"),
            ft.dropdown.Option("개조"),
            ft.dropdown.Option("설치"),
            ft.dropdown.Option("파라메터"),
            ft.dropdown.Option("펌웨어"),
            ft.dropdown.Option("기타"),
        ],
    )

    second_menu = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("2. 작업 정보", size=24, weight=ft.FontWeight.BOLD),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(po_code, col={"md": 6}),
                            ft.Container(work_type, col={"md": 6}),
                        ]
                    ),
                ]
            )
        )
    )

    # =========================================================
    # 세번째 메뉴
    # =========================================================
    equipment_cards = []
    eq_controls = []

    for i in range(1, 5):
        eq_code = ft.TextField(label="장비코드")
        eq_error = ft.TextField(label="Error현상", multiline=True, min_lines=2)
        eq_work = ft.TextField(label="작업내용", multiline=True, min_lines=3)
        eq_lp = ft.TextField(label="LP타입")
        eq_mfg = ft.TextField(label="MFGNO")
        eq_date = ft.TextField(label="제조일자")
        eq_fw = ft.TextField(label="F/W")

        eq_controls.append({
            "code": eq_code, "error": eq_error, "work": eq_work,
            "lp": eq_lp, "mfg": eq_mfg, "date": eq_date, "fw": eq_fw,
        })

        visible_state = True if i == 1 else False

        equipment_content = ft.Column(
            visible=visible_state,
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(eq_code, col={"md": 6}),
                        ft.Container(eq_lp, col={"md": 6}),
                    ]
                ),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(eq_mfg, col={"md": 4}),
                        ft.Container(eq_date, col={"md": 4}),
                        ft.Container(eq_fw, col={"md": 4}),
                    ]
                ),
                eq_error,
                eq_work,
            ]
        )

        if i == 1:
            card_toggle_btn = ft.Container(width=40)
        else:
            card_toggle_btn = ft.GestureDetector(
                content=ft.Row([ft.Text("[ 펼치기 ]", color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)]),
                mouse_cursor="pointer",
            )
            card_toggle_btn.on_tap = lambda e, panel=equipment_content, btn=card_toggle_btn: toggle_section(e, panel, btn)

        equipment_card = ft.Card(
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"3-{i}. 장비 정보", size=22, weight=ft.FontWeight.BOLD),
                                card_toggle_btn,
                            ]
                        ),
                        equipment_content,
                    ]
                )
            )
        )
        equipment_cards.append(equipment_card)

    # =========================================================
    # 네번째 메뉴 (화면 해상도 가변 대응 레이아웃 엔진)
    # =========================================================
    work_rows = []

    # 4개의 데이터 입력 컨트롤 사전 생성
    for i in range(4):
        div_text = "Regular" if i < 2 else "Overtime"
        work_rows.append({
            "div_text": div_text,
            "worker": ft.TextField(label="작업자", text_align=ft.TextAlign.CENTER),
            "start": ft.TextField(label="Start Time", text_align=ft.TextAlign.CENTER),
            "end": ft.TextField(label="End Time", text_align=ft.TextAlign.CENTER),
            "hour": ft.TextField(label="Working Hr", text_align=ft.TextAlign.CENTER),
            "travel": ft.TextField(label="Travel", text_align=ft.TextAlign.CENTER),
            "rate": ft.TextField(label="Hourly Rate", text_align=ft.TextAlign.CENTER),
        })

    total_amount = ft.TextField(label="Total Amount", width=320, height=80, text_align=ft.TextAlign.CENTER)

    # 실시간 렌더링을 담당할 동적 컨테이너 구성원 생성
    dynamic_table_container = ft.Column()

    def build_responsive_layout(page_width):
        dynamic_table_container.controls.clear()

        if page_width > 850:
            for row in work_rows:
                row["worker"].label = None;
                row["start"].label = None;
                row["end"].label = None
                row["hour"].label = None;
                row["travel"].label = None;
                row["rate"].label = None

            label_row = ft.ResponsiveRow(
                controls=[
                    ft.Container(ft.Text("구분", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 1.5}),
                    ft.Container(ft.Text("작업자", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 2}),
                    ft.Container(ft.Text("Start Time", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 2}),
                    ft.Container(ft.Text("End Time", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 2}),
                    ft.Container(ft.Text("Working Hr", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 1.2}),
                    ft.Container(ft.Text("Travel", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 1.2}),
                    ft.Container(ft.Text("Hourly Rate", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD), col={"md": 2.1}),
                ]
            )

            regular_section = ft.ResponsiveRow(
                controls=[
                    ft.Container(ft.TextField(value="Regular", read_only=True, text_align=ft.TextAlign.CENTER, expand=True, multiline=True), col={"md": 1.5}, height=110,
                                 alignment=ft.Alignment(0, 0)),
                    ft.Container(
                        col={"md": 10.5},
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.ResponsiveRow([
                                    ft.Container(work_rows[0]["worker"], col={"md": 2.28}), ft.Container(work_rows[0]["start"], col={"md": 2.28}),
                                    ft.Container(work_rows[0]["end"], col={"md": 2.28}), ft.Container(work_rows[0]["hour"], col={"md": 1.37}),
                                    ft.Container(work_rows[0]["travel"], col={"md": 1.37}), ft.Container(work_rows[0]["rate"], col={"md": 2.4}),
                                ]),
                                ft.ResponsiveRow([
                                    ft.Container(work_rows[1]["worker"], col={"md": 2.28}), ft.Container(work_rows[1]["start"], col={"md": 2.28}),
                                    ft.Container(work_rows[1]["end"], col={"md": 2.28}), ft.Container(work_rows[1]["hour"], col={"md": 1.37}),
                                    ft.Container(work_rows[1]["travel"], col={"md": 1.37}), ft.Container(work_rows[1]["rate"], col={"md": 2.4}),
                                ]),
                            ]
                        )
                    )
                ]
            )

            overtime_section = ft.ResponsiveRow(
                controls=[
                    ft.Container(ft.TextField(value="Overtime", read_only=True, text_align=ft.TextAlign.CENTER, expand=True, multiline=True), col={"md": 1.5}, height=110,
                                 alignment=ft.Alignment(0, 0)),
                    ft.Container(
                        col={"md": 10.5},
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.ResponsiveRow([
                                    ft.Container(work_rows[2]["worker"], col={"md": 2.28}), ft.Container(work_rows[2]["start"], col={"md": 2.28}),
                                    ft.Container(work_rows[2]["end"], col={"md": 2.28}), ft.Container(work_rows[2]["hour"], col={"md": 1.37}),
                                    ft.Container(work_rows[2]["travel"], col={"md": 1.37}), ft.Container(work_rows[2]["rate"], col={"md": 2.4}),
                                ]),
                                ft.ResponsiveRow([
                                    ft.Container(work_rows[3]["worker"], col={"md": 2.28}), ft.Container(work_rows[3]["start"], col={"md": 2.28}),
                                    ft.Container(work_rows[3]["end"], col={"md": 2.28}), ft.Container(work_rows[3]["hour"], col={"md": 1.37}),
                                    ft.Container(work_rows[3]["travel"], col={"md": 1.37}), ft.Container(work_rows[3]["rate"], col={"md": 2.4}),
                                ]),
                            ]
                        )
                    )
                ]
            )

            dynamic_table_container.controls.extend([label_row, ft.Container(height=5), regular_section, ft.Container(height=5), overtime_section])

        else:
            mobile_controls = []
            for idx, row in enumerate(work_rows):
                row["worker"].label = "작업자"
                row["start"].label = "Start Time"
                row["end"].label = "End Time"
                row["hour"].label = "Working Hr"
                row["travel"].label = "Travel"
                row["rate"].label = "Hourly Rate"

                card_item = ft.Container(
                    padding=12,
                    border=ft.Border.all(1, ft.Colors.BLACK12),
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_50,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.TIMER if "Regular" in row["div_text"] else ft.Icons.MORE_TIME,
                                    color=ft.Colors.BLUE if "Regular" in row["div_text"] else ft.Colors.ORANGE_700),
                            ft.Text(f"{row['div_text']} - 작업자 명단 #{(idx % 2) + 1}", weight=ft.FontWeight.BOLD, size=16)
                        ]),
                        ft.ResponsiveRow([
                            ft.Container(row["worker"], col={"xs": 12, "sm": 6}),
                            ft.Container(row["start"], col={"xs": 6, "sm": 3}),
                            ft.Container(row["end"], col={"xs": 6, "sm": 3}),
                        ]),
                        ft.ResponsiveRow([
                            ft.Container(row["hour"], col={"xs": 4}),
                            ft.Container(row["travel"], col={"xs": 4}),
                            ft.Container(row["rate"], col={"xs": 4}),
                        ])
                    ], spacing=10)
                )
                mobile_controls.append(card_item)
                mobile_controls.append(ft.Container(height=5))

            dynamic_table_container.controls.extend(mobile_controls)

    build_responsive_layout(page.width if page.width else 1000)

    def page_resize_handler(e):
        build_responsive_layout(page.width)
        page.update()

    page.on_resize = page_resize_handler

    fourth_menu = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("4. 작업 시간 및 비용", size=24, weight=ft.FontWeight.BOLD),
                    dynamic_table_container,
                    ft.Row(alignment=ft.MainAxisAlignment.END, controls=[total_amount])
                ]
            )
        )
    )

    # =========================================================
    # 다섯번째 메뉴
    # =========================================================
    warranty_inside = ft.Checkbox(label="보증내")
    warranty_outside = ft.Checkbox(label="보증외")
    paid_service = ft.Checkbox(label="유상")
    free_service = ft.Checkbox(label="무상")

    def warranty_inside_changed(e):
        if warranty_inside.value: warranty_outside.value = False
        page.update()

    def warranty_outside_changed(e):
        if warranty_outside.value: warranty_inside.value = False
        page.update()

    warranty_inside.on_change = warranty_inside_changed
    warranty_outside.on_change = warranty_outside_changed

    def paid_service_changed(e):
        if paid_service.value: free_service.value = False
        page.update()

    def free_service_changed(e):
        if free_service.value: paid_service.value = False
        page.update()

    paid_service.on_change = paid_service_changed
    free_service.on_change = free_service_changed

    fifth_menu = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("5. 보증 및 비용 구분", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row(controls=[ft.Text("보증기간", size=18, weight=ft.FontWeight.BOLD), warranty_inside, warranty_outside]),
                    ft.Row(controls=[ft.Text("비용지불", size=18, weight=ft.FontWeight.BOLD), paid_service, free_service]),
                ]
            )
        )
    )

    result_text = ft.Text(size=18)

    # =========================================================
    # 저장 함수
    # =========================================================
    def save_data(e):
        data = {
            "inspect_date": inspect_date.value if inspect_date.value else "",
            "fab": fab.value if fab.value else "",
            "process": process.value if process.value else "",
            "manager": manager.value if manager.value else "",
            "company": company.value if company.value else "",
            "requester": requester.value if requester.value else "",
            "writer": writer.value if writer.value else "",
            "po_code": po_code.value if po_code.value else "",
            "work_type": work_type.value if work_type.value else "",

            "eq1_code": eq_controls[0]["code"].value if eq_controls[0]["code"].value else "",
            "eq1_error": eq_controls[0]["error"].value if eq_controls[0]["error"].value else "",
            "eq1_work": eq_controls[0]["work"].value if eq_controls[0]["work"].value else "",
            "eq1_lp": eq_controls[0]["lp"].value if eq_controls[0]["lp"].value else "",
            "eq1_mfg": eq_controls[0]["mfg"].value if eq_controls[0]["mfg"].value else "",
            "eq1_date": eq_controls[0]["date"].value if eq_controls[0]["date"].value else "",
            "eq1_fw": eq_controls[0]["fw"].value if eq_controls[0]["fw"].value else "",

            "eq2_code": eq_controls[1]["code"].value if eq_controls[1]["code"].value else "",
            "eq2_error": eq_controls[1]["error"].value if eq_controls[1]["error"].value else "",
            "eq2_work": eq_controls[1]["work"].value if eq_controls[1]["work"].value else "",
            "eq2_lp": eq_controls[1]["lp"].value if eq_controls[1]["lp"].value else "",
            "eq2_mfg": eq_controls[1]["mfg"].value if eq_controls[1]["mfg"].value else "",
            "eq2_date": ft.TextField(label="제조일자"),
            "eq2_fw": eq_controls[1]["fw"].value if eq_controls[1]["fw"].value else "",

            "eq3_code": eq_controls[2]["code"].value if eq_controls[2]["code"].value else "",
            "eq3_error": eq_controls[2]["error"].value if eq_controls[2]["error"].value else "",
            "eq3_work": eq_controls[2]["work"].value if eq_controls[2]["work"].value else "",
            "eq3_lp": eq_controls[2]["lp"].value if eq_controls[2]["lp"].value else "",
            "eq3_mfg": eq_controls[2]["mfg"].value if eq_controls[2]["mfg"].value else "",
            "eq3_date": eq_controls[2]["date"].value if eq_controls[2]["date"].value else "",
            "eq3_fw": eq_controls[2]["fw"].value if eq_controls[2]["fw"].value else "",

            "eq4_code": eq_controls[3]["code"].value if eq_controls[3]["code"].value else "",
            "eq4_error": eq_controls[3]["error"].value if eq_controls[3]["error"].value else "",
            "eq4_work": eq_controls[3]["work"].value if eq_controls[3]["work"].value else "",
            "eq4_lp": eq_controls[3]["lp"].value if eq_controls[3]["lp"].value else "",
            "eq4_mfg": eq_controls[3]["mfg"].value if eq_controls[3]["mfg"].value else "",
            "eq4_date": eq_controls[3]["date"].value if eq_controls[3]["date"].value else "",
            "eq4_fw": eq_controls[3]["fw"].value if eq_controls[3]["fw"].value else "",

            "div1": "Regular",
            "worker1": work_rows[0]["worker"].value if work_rows[0]["worker"].value else "",
            "start1": work_rows[0]["start"].value if work_rows[0]["start"].value else "",
            "end1": work_rows[0]["end"].value if work_rows[0]["end"].value else "",
            "hour1": work_rows[0]["hour"].value if work_rows[0]["hour"].value else "",
            "travel1": work_rows[0]["travel"].value if work_rows[0]["travel"].value else "",
            "rate1": work_rows[0]["rate"].value if work_rows[0]["rate"].value else "",

            "div2": "Regular",
            "worker2": work_rows[1]["worker"].value if work_rows[1]["worker"].value else "",
            "start2": work_rows[1]["start"].value if work_rows[1]["start"].value else "",
            "end2": work_rows[1]["end"].value if work_rows[1]["end"].value else "",
            "hour2": work_rows[1]["hour"].value if work_rows[1]["hour"].value else "",
            "travel2": work_rows[1]["travel"].value if work_rows[1]["travel"].value else "",
            "rate2": work_rows[1]["rate"].value if work_rows[1]["rate"].value else "",

            "div3": "Overtime",
            "worker3": work_rows[2]["worker"].value if work_rows[2]["worker"].value else "",
            "start3": work_rows[2]["start"].value if work_rows[2]["start"].value else "",
            "end3": work_rows[2]["end"].value if work_rows[2]["end"].value else "",
            "hour3": work_rows[2]["hour"].value if work_rows[2]["hour"].value else "",
            "travel3": work_rows[2]["travel"].value if work_rows[2]["travel"].value else "",
            "rate3": work_rows[2]["rate"].value if work_rows[2]["rate"].value else "",

            "div4": "Overtime",
            "worker4": work_rows[3]["worker"].value if work_rows[3]["worker"].value else "",
            "start4": work_rows[3]["start"].value if work_rows[3]["start"].value else "",
            "end4": work_rows[3]["end"].value if work_rows[3]["end"].value else "",
            "hour4": work_rows[3]["hour"].value if work_rows[3]["hour"].value else "",
            "travel4": work_rows[3]["travel"].value if work_rows[3]["travel"].value else "",
            "rate4": work_rows[3]["rate"].value if work_rows[3]["rate"].value else "",

            "total_amount": total_amount.value if total_amount.value else "",
            "warranty": "보증내" if warranty_inside.value else "보증외",
            "payment": "유상" if paid_service.value else "무상",
        }

        try:
            result_text.value = "데이터 전송 중..."
            result_text.color = ft.Colors.BLUE
            page.update()

            # ⭐️ 안드로이드 환경에 친화적인 requests.post 방식으로 교체 (지연 및 먹통 최소화)
            response = requests.post(SCRIPT_URL, json=data, timeout=15)

            if response.status_code == 200:
                result_text.value = "Google Sheet 저장 완료!"
                result_text.color = ft.Colors.GREEN

                # 입력 폼 초기화
                inspect_date.value = ""; fab.value = ""; process.value = ""
                manager.value = ""; company.value = ""; requester.value = ""; writer.value = ""
                po_code.value = ""; work_type.value = None

                for eq in eq_controls:
                    eq["code"].value = ""; eq["error"].value = ""; eq["work"].value = ""
                    eq["lp"].value = ""; eq["mfg"].value = ""; eq["date"].value = ""; eq["fw"].value = ""

                for row in work_rows:
                    row["worker"].value = ""; row["start"].value = ""; row["end"].value = ""
                    row["hour"].value = ""; row["travel"].value = ""; row["rate"].value = ""

                total_amount.value = ""
                warranty_inside.value = False; warranty_outside.value = False
                paid_service.value = False; free_service.value = False
            else:
                result_text.value = f"저장 실패 (오류 코드: {response.status_code})"
                result_text.color = ft.Colors.RED
        except Exception as ex:
            result_text.value = f"통신 에러 발생 : {ex}"
            result_text.color = ft.Colors.RED

        page.update()

    # =========================================================
    # 저장 버튼
    # =========================================================
    save_button = ft.ElevatedButton(
        content=ft.Text("저장"),
        width=180,
        height=50,
        on_click=save_data,
    )

    # =========================================================
    # 전체 UI 배치
    # =========================================================
    page.add(
        ft.Column(
            spacing=20,
            controls=[
                ft.Text("장비 점검 관리 프로그램", size=32, weight=ft.FontWeight.BOLD),
                first_menu,
                second_menu,
                *equipment_cards,
                fourth_menu,
                fifth_menu,
                ft.Row(alignment=ft.MainAxisAlignment.END, controls=[save_button]),
                result_text,
            ]
        )
    )


ft.run(main)