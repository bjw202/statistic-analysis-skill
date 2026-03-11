#!/usr/bin/env python3
"""Excel data loader with summary output for the statistic-analysis skill."""

import argparse
import os
import sys

import numpy as np
import pandas as pd


def load_excel(file_path: str, sheet_name: str | None = None) -> pd.DataFrame:
    """
    Load an Excel file and return a DataFrame.

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
            # Try 'Data' sheet first, then fall back to first sheet
            if "Data" in available_sheets:
                target_sheet = "Data"
            else:
                target_sheet = available_sheets[0]

        df = pd.read_excel(file_path, sheet_name=target_sheet)
        return df

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

    # Determine which sheet was loaded
    try:
        xl = pd.ExcelFile(file_path)
        available_sheets = xl.sheet_names
        if sheet_name is not None:
            used_sheet = sheet_name
        elif "Data" in available_sheets:
            used_sheet = "Data"
        else:
            used_sheet = available_sheets[0]
    except Exception:
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
