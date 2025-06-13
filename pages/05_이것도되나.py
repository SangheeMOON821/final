import streamlit as st
from io import BytesIO
import re
from openpyxl import load_workbook, Workbook
from copy import copy

st.title("엑셀 파일 → 시트 병합기 (완전 스타일 보존)")

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
    target_wb = Workbook()
    target_wb.remove(target_wb.active)

    for uploaded_file in uploaded_files:
        try:
            src_wb = load_workbook(uploaded_file, data_only=False)
            src_sheet = src_wb[src_wb.sheetnames[0]]
            base = uploaded_file.name.rsplit('.', 1)[0]
            title = sanitize_sheet_name(base)
            tgt_sheet = target_wb.create_sheet(title=title)

            # 기본 행 높이·열 너비 복사
            tgt_sheet.sheet_format.defaultRowHeight = src_sheet.sheet_format.defaultRowHeight
            tgt_sheet.sheet_format.defaultColWidth = src_sheet.sheet_format.defaultColWidth

            # 열 너비·숨김·outlineLevel 복사
            for col_letter, src_dim in src_sheet.column_dimensions.items():
                tgt_dim = tgt_sheet.column_dimensions[col_letter]
                tgt_dim.width = src_dim.width
                tgt_dim.hidden = src_dim.hidden
                tgt_dim.outlineLevel = src_dim.outlineLevel
                tgt_dim.bestFit = src_dim.bestFit

            # 행 높이·숨김·outlineLevel 복사
            for row_idx, src_dim in src_sheet.row_dimensions.items():
                tgt_dim = tgt_sheet.row_dimensions[row_idx]
                if src_dim.height is not None:
                    tgt_dim.height = src_dim.height
                tgt_dim.hidden = src_dim.hidden
                tgt_dim.outlineLevel = src_dim.outlineLevel

            # 병합 셀 복사
            for merged in src_sheet.merged_cells.ranges:
                tgt_sheet.merge_cells(str(merged))

            # Freeze panes 복사
            tgt_sheet.freeze_panes = src_sheet.freeze_panes

            # 셀 값·스타일 복사
            for row in src_sheet.iter_rows():
                for cell in row:
                    new_cell = tgt_sheet.cell(
                        row=cell.row, column=cell.column, value=cell.value
                    )
                    if cell.has_style:
                        new_cell.font = copy(cell.font)
                        new_cell.border = copy(cell.border)
                        new_cell.fill = copy(cell.fill)
                        new_cell.number_format = cell.number_format
                        new_cell.protection = copy(cell.protection)
                        new_cell.alignment = copy(cell.alignment)

        except Exception as e:
            st.error(f"{uploaded_file.name} 읽기 실패: {e}")

    target_wb.save(output)
    output.seek(0)

    st.success(f"{len(uploaded_files)}개의 파일이 완전 스타일 보존하여 병합되었습니다!")
    st.download_button(
        label="엑셀로 다운로드",
        data=output.getvalue(),
        file_name="시트별_스타일_완전_보존_병합.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
