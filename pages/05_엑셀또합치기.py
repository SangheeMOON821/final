import streamlit as st
from io import BytesIO
import re
from openpyxl import load_workbook, Workbook
from copy import copy

st.title("엑셀 파일 → 시트 병합기 (스타일 보존)")

uploaded_files = st.file_uploader(
    "엑셀 파일을 여러 개 업로드하세요", 
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

def sanitize_sheet_name(name):
    # Excel 시트명은 최대 31자, 특수문자 불가
    name = re.sub(r'[:\\/?*\[\]]', '', name)
    return name[:31]

if uploaded_files:
    output = BytesIO()
    # 새 워크북 생성 후 기본 시트 제거
    target_wb = Workbook()
    target_wb.remove(target_wb.active)

    for uploaded_file in uploaded_files:
        try:
            source_wb = load_workbook(uploaded_file, data_only=False)
            # 첫 번째 시트만 복제
            source_sheet = source_wb[source_wb.sheetnames[0]]
            base_name = uploaded_file.name.rsplit('.', 1)[0]
            sheet_name = sanitize_sheet_name(base_name)
            ws = target_wb.create_sheet(title=sheet_name)

            # 열 너비 복사
            for col, dim in source_sheet.column_dimensions.items():
                ws.column_dimensions[col].width = dim.width

            # 행 높이 복사
            for row, dim in source_sheet.row_dimensions.items():
                if dim.height:
                    ws.row_dimensions[row].height = dim.height

            # 병합 셀 복사
            for merged in source_sheet.merged_cells.ranges:
                ws.merge_cells(str(merged))

            # Freeze panes 복사
            ws.freeze_panes = source_sheet.freeze_panes

            # 셀 값·스타일 복사
            for row in source_sheet.iter_rows():
                for cell in row:
                    new_cell = ws.cell(row=cell.row, column=cell.column, value=cell.value)
                    if cell.has_style:
                        new_cell.font = copy(cell.font)
                        new_cell.border = copy(cell.border)
                        new_cell.fill = copy(cell.fill)
                        # number_format은 문자열이므로 바로 할당해도 무방
                        new_cell.number_format = cell.number_format
                        new_cell.protection = copy(cell.protection)
                        new_cell.alignment = copy(cell.alignment)

        except Exception as e:
            st.error(f"{uploaded_file.name} 읽기 실패: {e}")

    # 결과 저장
    target_wb.save(output)
    output.seek(0)

    st.success(f"{len(uploaded_files)}개의 파일이 스타일까지 보존하여 병합되었습니다!")

    st.download_button(
        label="엑셀로 다운로드",
        data=output.getvalue(),
        file_name="시트별_스타일_보존_병합.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
