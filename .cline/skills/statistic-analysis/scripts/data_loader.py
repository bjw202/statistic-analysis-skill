#!/usr/bin/env python3
"""Excel data loader with summary output for the statistic-analysis skill.

[회사 환경 안내]
이 스크립트는 DRM이 적용된 회사 Excel 파일을 읽기 위해
win32com (Excel COM 자동화) 방식을 사용합니다.

필수 조건:
  - Windows 환경
  - Microsoft Excel 설치됨
  - 회사 보안 시스템(DRM)에 로그인된 상태

문제 발생 시 확인 사항:
  [TROUBLESHOOT-1] win32com import 실패
    → 원인: pywin32 패키지 미설치
    → 해결: pip install pywin32

  [TROUBLESHOOT-2] Excel 파일이 열리지 않음 (pywintypes.com_error)
    → 원인: DRM 미로그인 또는 파일 경로 오류
    → 해결: 회사 보안 솔루션에 로그인 후 재시도

  [TROUBLESHOOT-3] 데이터가 비어있거나 None만 반환됨
    → 원인: UsedRange 인식 오류 (Excel 파일 포맷 이슈)
    → 해결: _win32com_sheet_to_dataframe() 내 데이터 파싱 로직 점검

  [TROUBLESHOOT-4] Excel 프로세스가 종료되지 않고 남음
    → 원인: 예외 발생 시 finally 블록 미실행 (드문 경우)
    → 해결: 작업관리자에서 EXCEL.EXE 수동 종료 후 재시도
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

# [WIN32COM-IMPORT]
# win32com은 Windows + pywin32 패키지 필요.
# 미설치 시 TROUBLESHOOT-1 참고.
try:
    import win32com.client
    import pywintypes
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False


def _get_available_sheets_win32com(excel_app: object, wb: object) -> list[str]:
    """
    [WIN32COM] 열린 워크북에서 시트 이름 목록을 반환합니다.

    문제 발생 시: [TROUBLESHOOT-2] 참고
    """
    # [SHEET-NAMES] Sheets.Count는 1-based index
    return [wb.Sheets(i + 1).Name for i in range(wb.Sheets.Count)]


def _win32com_sheet_to_dataframe(ws: object) -> pd.DataFrame:
    """
    [WIN32COM] Excel 워크시트 객체를 pandas DataFrame으로 변환합니다.

    UsedRange.Value로 전체 사용 영역을 한 번에 읽어 DataFrame을 구성합니다.
    첫 번째 행을 컬럼 헤더로 사용합니다.

    문제 발생 시: [TROUBLESHOOT-3] 참고

    Args:
        ws: win32com Worksheet 객체

    Returns:
        첫 행을 헤더로 한 DataFrame. None 값은 float('nan')으로 변환됨.
    """
    # [USEDRANGE] UsedRange.Value는 tuple of tuples 반환 (행 × 열)
    # 단일 셀이면 스칼라, 단일 행/열이면 1D tuple이 될 수 있음
    raw = ws.UsedRange.Value

    if raw is None:
        # [TROUBLESHOOT-3] 시트가 비어있는 경우
        return pd.DataFrame()

    # 2D tuple 정규화: 단일 행이면 감싸서 2D로 만들기
    if not isinstance(raw[0], tuple):
        raw = (raw,)

    headers = [str(cell) if cell is not None else f"Col_{i}" for i, cell in enumerate(raw[0])]

    rows = []
    for row in raw[1:]:
        # [NULL-HANDLING] COM에서 빈 셀은 None으로 옴 → float('nan')으로 변환
        rows.append([float("nan") if cell is None else cell for cell in row])

    return pd.DataFrame(rows, columns=headers)


def _load_excel_win32com(file_path: str, sheet_name: str | None = None) -> tuple[pd.DataFrame, str]:
    """
    [WIN32COM] DRM 보호 Excel 파일을 COM 자동화로 읽어 DataFrame을 반환합니다.

    Excel 프로세스를 백그라운드로 실행하고, 데이터를 읽은 후 반드시 종료합니다.

    Args:
        file_path: Excel 파일 경로 (절대 경로로 자동 변환됨)
        sheet_name: 읽을 시트 이름. None이면 'Data' → 첫 번째 시트 순으로 시도.

    Returns:
        (DataFrame, 실제_사용된_시트명) 튜플

    Raises:
        FileNotFoundError: 파일 없음
        ValueError: 지정한 시트 없음
        RuntimeError: COM 오류 (DRM 미로그인 등)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    # [ABS-PATH] win32com은 절대 경로 필요
    abs_path = os.path.abspath(file_path)

    # [EXCEL-INIT] Excel 애플리케이션을 백그라운드(비표시)로 실행
    # Visible=False: 화면에 Excel 창이 뜨지 않음
    # DisplayAlerts=False: 팝업 다이얼로그 자동 무시
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = None
    try:
        # [OPEN-WORKBOOK] DRM 파일은 회사 보안 솔루션 로그인 상태에서만 열림
        # 오류 발생 시 TROUBLESHOOT-2 참고
        wb = excel.Workbooks.Open(abs_path)

        available_sheets = _get_available_sheets_win32com(excel, wb)

        # 대상 시트 결정
        if sheet_name is not None:
            if sheet_name not in available_sheets:
                raise ValueError(
                    f"시트를 찾을 수 없습니다: '{sheet_name}'. "
                    f"사용 가능한 시트: {available_sheets}"
                )
            target_sheet = sheet_name
        else:
            # 'Data' 시트 우선, 없으면 첫 번째 시트 사용
            target_sheet = "Data" if "Data" in available_sheets else available_sheets[0]

        ws = wb.Sheets(target_sheet)
        df = _win32com_sheet_to_dataframe(ws)
        return df, target_sheet

    except pywintypes.com_error as e:
        # [COM-ERROR] DRM 미로그인, 파일 손상, Excel 미설치 등
        # TROUBLESHOOT-2 참고
        raise RuntimeError(
            f"Excel COM 오류 (DRM 로그인 상태 확인 필요): {e}"
        ) from e

    finally:
        # [CLEANUP] Excel 프로세스 반드시 종료 (메모리 누수 방지)
        # TROUBLESHOOT-4: 이 블록이 실행되지 않으면 EXCEL.EXE 수동 종료 필요
        if wb is not None:
            wb.Close(SaveChanges=False)
        excel.Quit()


def load_excel(file_path: str, sheet_name: str | None = None) -> pd.DataFrame:
    """
    Load an Excel file and return a DataFrame.

    [회사 환경] DRM 보호 파일을 위해 win32com(Excel COM) 방식을 사용합니다.
    win32com 사용 불가 환경(비Windows 등)에서는 pandas fallback을 시도합니다.

    Tries to load the sheet named 'Data' first, then falls back to the first sheet.
    Columns may have different numbers of valid values due to NaN padding.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Optional sheet name. If None, tries 'Data' then first sheet.

    Returns:
        DataFrame with all columns loaded (NaN preserved for missing values).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the sheet cannot be found.
        RuntimeError: If both win32com and pandas fail to load the file.
    """
    if not WIN32COM_AVAILABLE:
        # [FALLBACK] 비Windows 환경이나 pywin32 미설치 시 pandas로 시도
        # 회사 DRM 환경에서는 이 경로로 진입하면 대부분 오류 발생 → TROUBLESHOOT-1 참고
        return _load_excel_pandas_fallback(file_path, sheet_name)

    try:
        df, _ = _load_excel_win32com(file_path, sheet_name)
        return df
    except (FileNotFoundError, ValueError):
        raise
    except RuntimeError:
        raise


def _load_excel_pandas_fallback(file_path: str, sheet_name: str | None = None) -> pd.DataFrame:
    """
    [FALLBACK] pandas로 Excel을 읽는 기존 방식.

    DRM이 없는 환경(개발PC, Mac 등) 또는 win32com 미설치 시 사용됩니다.
    회사 DRM 파일에는 작동하지 않습니다.

    문제 발생 시: win32com 방식(_load_excel_win32com)으로 전환하세요.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    try:
        xl = pd.ExcelFile(file_path)
        available_sheets = xl.sheet_names

        if sheet_name is not None:
            if sheet_name not in available_sheets:
                raise ValueError(
                    f"시트를 찾을 수 없습니다: '{sheet_name}'. "
                    f"사용 가능한 시트: {available_sheets}"
                )
            target_sheet = sheet_name
        else:
            target_sheet = "Data" if "Data" in available_sheets else available_sheets[0]

        return pd.read_excel(file_path, sheet_name=target_sheet)

    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise RuntimeError(f"Excel 파일 로드 중 오류 발생: {e}") from e


def summarize(df: pd.DataFrame) -> dict:
    """
    Compute per-column summary statistics.

    Args:
        df: DataFrame to summarize.

    Returns:
        Dict with key 'columns', a list of per-column summary dicts:
        [{name, count, mean, std, min, max, missing}, ...]
    """
    columns_info = []
    for col in df.columns:
        series = df[col]
        numeric_series = pd.to_numeric(series, errors="coerce")
        valid = numeric_series.dropna()
        total_rows = len(series)
        missing_count = total_rows - len(valid)

        if len(valid) > 0:
            col_info = {
                "name": str(col),
                "count": int(len(valid)),
                "mean": float(valid.mean()),
                "std": float(valid.std()) if len(valid) > 1 else 0.0,
                "min": float(valid.min()),
                "max": float(valid.max()),
                "missing": int(missing_count),
                "is_numeric": True,
            }
        else:
            col_info = {
                "name": str(col),
                "count": 0,
                "mean": None,
                "std": None,
                "min": None,
                "max": None,
                "missing": int(missing_count),
                "is_numeric": False,
            }
        columns_info.append(col_info)

    return {"columns": columns_info}


def validate_numeric(df: pd.DataFrame) -> list[str]:
    """
    Identify non-numeric columns in the DataFrame.

    Args:
        df: DataFrame to check.

    Returns:
        List of column names that cannot be converted to numeric.
    """
    non_numeric = []
    for col in df.columns:
        numeric_series = pd.to_numeric(df[col], errors="coerce")
        valid_count = numeric_series.notna().sum()
        if valid_count == 0:
            non_numeric.append(str(col))
    return non_numeric


def print_summary(file_path: str, sheet_name: str | None = None) -> None:
    """
    Print a human-readable summary of the Excel file to stdout.

    Output format:
        === 데이터 요약 ===
        파일: ftg.xlsx
        시트: Data
        행 수: 29

        열 목록:
          Ref    | N=29 | 평균=0.97 | 표준편차=0.23 | 범위=[0.83, 1.99] | 결측=0
          ...

        첫 3개 행:
          Ref   Cond.1  Cond.2  ...

    Args:
        file_path: Path to the Excel file.
        sheet_name: Optional sheet name.
    """
    try:
        df = load_excel(file_path, sheet_name)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)

    # [SHEET-NAME-DETECT] 실제 로드된 시트명 확인
    # win32com 방식은 _load_excel_win32com에서 시트명을 반환하지만,
    # load_excel()이 시트명을 노출하지 않으므로 여기서 재확인합니다.
    # [FIX-HINT] 시트명이 "Unknown"으로 표시된다면 아래 로직을 수정하세요.
    used_sheet = sheet_name or "Unknown"
    try:
        if WIN32COM_AVAILABLE:
            # [WIN32COM] 시트 목록을 COM으로 가져옴
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            wb = None
            try:
                wb = excel.Workbooks.Open(os.path.abspath(file_path))
                available_sheets = _get_available_sheets_win32com(excel, wb)
                used_sheet = sheet_name or ("Data" if "Data" in available_sheets else available_sheets[0])
            finally:
                if wb is not None:
                    wb.Close(SaveChanges=False)
                excel.Quit()
        else:
            # [FALLBACK] pandas로 시트 목록 확인
            xl = pd.ExcelFile(file_path)
            available_sheets = xl.sheet_names
            used_sheet = sheet_name or ("Data" if "Data" in available_sheets else available_sheets[0])
    except Exception:
        # [GRACEFUL-DEGRADATION] 시트명 확인 실패해도 요약 출력은 계속 진행
        used_sheet = sheet_name or "Unknown"

    summary = summarize(df)
    non_numeric = validate_numeric(df)

    print("=== 데이터 요약 ===")
    print(f"파일: {os.path.basename(file_path)}")
    print(f"시트: {used_sheet}")
    print(f"행 수: {len(df)}")
    print(f"열 수: {len(df.columns)}")

    if non_numeric:
        print(f"\n경고: 비수치형 열 감지됨: {non_numeric}")

    print("\n열 목록:")
    for col_info in summary["columns"]:
        name = col_info["name"]
        if col_info["is_numeric"]:
            print(
                f"  {name:<12} | N={col_info['count']}"
                f" | 평균={col_info['mean']:.3f}"
                f" | 표준편차={col_info['std']:.3f}"
                f" | 범위=[{col_info['min']:.3f}, {col_info['max']:.3f}]"
                f" | 결측={col_info['missing']}"
            )
        else:
            print(
                f"  {name:<12} | N=0 (비수치형)"
                f" | 결측={col_info['missing']}"
            )

    # Show first 3 rows preview
    print("\n첫 3개 행:")
    preview = df.head(3)
    # Format for display
    col_widths = {col: max(len(str(col)), 8) for col in df.columns}
    header = "  " + "  ".join(str(col).ljust(col_widths[col]) for col in df.columns)
    print(header)
    for _, row in preview.iterrows():
        formatted_vals = []
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                formatted_vals.append("NaN".ljust(col_widths[col]))
            elif isinstance(val, float):
                formatted_vals.append(f"{val:.3f}".ljust(col_widths[col]))
            else:
                formatted_vals.append(str(val).ljust(col_widths[col]))
        print("  " + "  ".join(formatted_vals))


def get_column_data(df: pd.DataFrame, column_name: str) -> np.ndarray:
    """
    Extract clean (non-NaN) numeric values from a column.

    Args:
        df: DataFrame.
        column_name: Column name to extract.

    Returns:
        numpy array of valid numeric values.
    """
    series = pd.to_numeric(df[column_name], errors="coerce")
    return series.dropna().to_numpy(dtype=float)


def main() -> None:
    """CLI entry point for data_loader.py."""
    parser = argparse.ArgumentParser(
        description="Excel 데이터 로더 — statistic-analysis 스킬용"
    )
    parser.add_argument("excel_path", help="Excel 파일 경로")
    parser.add_argument("--sheet", default=None, help="시트 이름 (기본값: 'Data' 또는 첫 번째 시트)")
    parser.add_argument("--summary", action="store_true", help="데이터 요약 출력")

    args = parser.parse_args()

    if args.summary:
        print_summary(args.excel_path, args.sheet)
    else:
        try:
            df = load_excel(args.excel_path, args.sheet)
            print(f"로드 완료: {len(df)} 행, {len(df.columns)} 열")
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            print(f"오류: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
