#!/usr/bin/env python3
"""Main orchestrator for statistical analysis. CLI entry point."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd

from data_loader import load_excel, get_column_data
from annotator import build_analysis_sets, load_config, detect_replicates
from analysis_engine import run_analysis
from visualizer import create_boxplot, create_significance_heatmap
from reporter import assemble_dashboard, save_report


def _determine_output_path(config: dict, excel_path: str) -> str:
    """
    Determine output path for the report based on config settings.

    Args:
        config: Analysis config dict.
        excel_path: Path to the input Excel file.

    Returns:
        Full path for the output Markdown report.
    """
    output_setting = config.get("analysis", {}).get("output_path", "")

    if not output_setting or output_setting in ("same_as_input", ""):
        # Same directory as Excel file
        base_dir = os.path.dirname(os.path.abspath(excel_path))
    elif output_setting == "cwd":
        base_dir = os.getcwd()
    else:
        base_dir = output_setting

    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "analysis_report.md")


def main() -> None:
    """
    Main entry point for the statistical analysis orchestrator.

    Usage:
        python3 statistic_analyzer.py <excel_path> <config_path>

    Outputs:
        JSON summary to stdout.
        analysis_report.md to the configured output directory.
    """
    parser = argparse.ArgumentParser(
        description="Statistical analysis orchestrator for Excel experimental data."
    )
    parser.add_argument("excel_path", help="Path to the Excel file (.xlsx)")
    parser.add_argument("config_path", help="Path to analysis_config.json")
    args = parser.parse_args()

    excel_path = args.excel_path
    config_path = args.config_path

    # --- Step 1: Load config ---
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        error_result = {"status": "error", "error": str(e)}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)
    except json.JSONDecodeError as e:
        error_result = {"status": "error", "error": f"설정 파일 JSON 파싱 오류: {e}"}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    alpha = config.get("analysis", {}).get("alpha", 0.05)

    # Store excel file path in config for reporter
    if "experiment" not in config:
        config["experiment"] = {}
    config["experiment"]["excel_file"] = os.path.basename(excel_path)

    # --- Step 2: Load Excel data ---
    sheet_name = config.get("experiment", {}).get("sheet_name", None)
    try:
        df = load_excel(excel_path, sheet_name)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        error_result = {"status": "error", "error": str(e)}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    # --- Step 3: Build analysis sets ---
    # Check if analysis sets are pre-specified in config
    existing_sets = config.get("analysis_sets", [])
    if existing_sets:
        analysis_sets = existing_sets
    else:
        analysis_sets = build_analysis_sets(config)

    if not analysis_sets:
        error_result = {
            "status": "error",
            "error": "분석 세트를 생성할 수 없습니다. 설정을 확인해주세요.",
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    # --- Step 3.5: Run factorial / factor impact analysis if applicable ---
    twoway_result = None
    factor_impact_results = []  # 풀링된 요인 분리 비교 결과

    # (A) 완전 설계: Two-Way ANOVA
    factorial_sets = [s for s in analysis_sets if s.get("type") == "twoway_anova"]
    if factorial_sets:
        fset = factorial_sets[0]
        columns_config_fa = config.get("columns", {})
        rows = []
        for col_name in fset.get("groups", []):
            col_info = columns_config_fa.get(col_name, {})
            factors = col_info.get("factors", {})
            if col_name not in df.columns:
                matches = [c for c in df.columns if str(c).strip().lower() == col_name.strip().lower()]
                col_actual = matches[0] if matches else None
            else:
                col_actual = col_name
            if col_actual is None:
                continue
            col_data = get_column_data(df, col_actual)
            for val in col_data:
                rows.append({**factors, "value": float(val), "source_column": col_name})
        if rows:
            df_long = pd.DataFrame(rows)
            factor_info = fset.get("factor_info", {})
            factor_names = list(factor_info.keys())
            if len(factor_names) >= 2:
                from analysis_engine import run_twoway_anova
                twoway_result = run_twoway_anova(df_long, factor_names[0], factor_names[1], "value", alpha)

    # (B) 불완전 설계: 풀링된 요인 분리 비교
    pooled_sets = [s for s in analysis_sets if s.get("type") == "factor_impact_pooled"]
    if pooled_sets:
        from analysis_engine import run_analysis as engine_run, compute_cohens_d

        for pset in pooled_sets:
            group_a_info = pset.get("group_a", {})
            group_b_info = pset.get("group_b", {})

            # 그룹 A 데이터 풀링
            data_a = []
            for col_name in group_a_info.get("columns", []):
                col_actual = col_name if col_name in df.columns else None
                if col_actual is None:
                    matches = [c for c in df.columns if str(c).strip().lower() == col_name.strip().lower()]
                    col_actual = matches[0] if matches else None
                if col_actual:
                    data_a.extend(get_column_data(df, col_actual).tolist())

            # 그룹 B 데이터 풀링
            data_b = []
            for col_name in group_b_info.get("columns", []):
                col_actual = col_name if col_name in df.columns else None
                if col_actual is None:
                    matches = [c for c in df.columns if str(c).strip().lower() == col_name.strip().lower()]
                    col_actual = matches[0] if matches else None
                if col_actual:
                    data_b.extend(get_column_data(df, col_actual).tolist())

            if len(data_a) >= 2 and len(data_b) >= 2:
                arr_a = np.array(data_a)
                arr_b = np.array(data_b)
                groups_dict = {
                    group_a_info.get("label", "A"): arr_a,
                    group_b_info.get("label", "B"): arr_b,
                }
                result = engine_run(groups_dict, alpha=alpha)
                result["analysis_set_id"] = pset.get("id")
                result["isolates_factor"] = pset.get("isolates_factor")
                result["pooled_n_a"] = len(data_a)
                result["pooled_n_b"] = len(data_b)
                result["pooled_cols_a"] = group_a_info.get("columns", [])
                result["pooled_cols_b"] = group_b_info.get("columns", [])
                factor_impact_results.append(result)

        # 요인 영향도 랭킹 생성 (Cohen's d 기반)
        if factor_impact_results:
            factor_ranking = []
            for fir in factor_impact_results:
                factor_name = fir.get("isolates_factor", "unknown")
                d = fir.get("cohens_d")
                p_val = fir.get("test_result", {}).get("p_value")
                is_sig = fir.get("is_significant", False)
                factor_ranking.append({
                    "factor": factor_name,
                    "cohens_d": abs(d) if d is not None else 0.0,
                    "p_value": p_val,
                    "is_significant": is_sig,
                    "test_display": fir.get("test_display", ""),
                })
            factor_ranking.sort(key=lambda x: x["cohens_d"], reverse=True)

            # twoway_result 형식으로 변환 (reporter 호환)
            twoway_result = {
                "method": "factor_isolation_pooled",
                "method_display": "요인 분리 풀링 비교 (반복실험 풀링 + 개별 요인 효과 비교)",
                "factor_ranking": factor_ranking,
                "factor_impact_results": factor_impact_results,
                "factors": {},
            }
            for fr in factor_ranking:
                twoway_result["factors"][fr["factor"]] = {
                    "cohens_d": fr["cohens_d"],
                    "p_value": fr["p_value"],
                    "is_significant": fr["is_significant"],
                    "test_display": fr["test_display"],
                }

    # (C) 요인 분석 시 pairwise vs control 상세 분석도 추가
    if factorial_sets or pooled_sets:
        columns_for_pairwise = config.get("columns", {})
        has_control = any(
            c.get("role") == "control" or c.get("is_control", False)
            for c in columns_for_pairwise.values()
        )
        if has_control:
            pairwise_config = {"analysis": {"primary_goal": "pairwise_vs_control"}, "columns": columns_for_pairwise}
            pairwise_sets = build_analysis_sets(pairwise_config)
            if pairwise_sets:
                analysis_sets = analysis_sets + pairwise_sets

    # --- Step 4: Run analysis for each set ---
    results = []
    plots: dict[str, bytes] = {}
    significant_set_ids = []

    columns_config = config.get("columns", {})

    for analysis_set in analysis_sets:
        # 요인 영향도 분석용 세트는 별도 처리했으므로 per-set 분석에서 제외
        if analysis_set.get("type") in ("twoway_anova", "factor_impact_pooled"):
            continue

        set_id = analysis_set.get("id", "unknown")
        groups_to_compare = analysis_set.get("groups", [])

        # Extract data for each group
        groups_dict = {}
        for col_name in groups_to_compare:
            if col_name not in df.columns:
                # Try case-insensitive match
                matches = [c for c in df.columns if str(c).strip().lower() == col_name.strip().lower()]
                if matches:
                    col_name_actual = matches[0]
                else:
                    print(
                        f"경고: 열 '{col_name}'을 찾을 수 없습니다. 분석 세트 '{set_id}'를 건너뜁니다.",
                        file=sys.stderr,
                    )
                    break
            else:
                col_name_actual = col_name

            data = get_column_data(df, col_name_actual)
            if len(data) >= 2:
                groups_dict[col_name] = data

        if len(groups_dict) < 2:
            results.append({
                "analysis_set_id": set_id,
                "error": f"유효한 데이터 그룹 수 부족 ({len(groups_dict)}개)",
                "is_significant": False,
            })
            continue

        # Run statistical analysis
        result = run_analysis(groups_dict, alpha=alpha)
        result["analysis_set_id"] = set_id

        # Determine significant pairs for plot brackets
        sig_pairs = []
        if result.get("is_significant") and len(groups_dict) == 2:
            group_names = list(groups_dict.keys())
            p_val = result.get("test_result", {}).get("p_value")
            if p_val is not None:
                sig_pairs.append((group_names[0], group_names[1], p_val))
        elif result.get("is_significant") and result.get("posthoc_matrix") is not None:
            # Multi-group: get significant pairs from post-hoc
            ph = result["posthoc_matrix"]
            if isinstance(ph, pd.DataFrame):
                cols = list(ph.columns)
                for i, c1 in enumerate(cols):
                    for c2 in cols[i + 1:]:
                        try:
                            p_val = float(ph.loc[c1, c2])
                            if p_val < alpha:
                                sig_pairs.append((c1, c2, p_val))
                        except (KeyError, TypeError, ValueError):
                            pass

        # Create box plot
        measurement_label = config.get("experiment", {}).get("description", "측정값")
        col_label = analysis_set.get("label", set_id)
        try:
            plot_bytes = create_boxplot(
                data_dict=groups_dict,
                title=col_label,
                y_label=measurement_label,
                sig_pairs=sig_pairs,
                alpha=alpha,
            )
            plots[set_id] = plot_bytes
        except Exception as e:
            print(f"경고: 플롯 생성 실패 ({set_id}): {e}", file=sys.stderr)

        results.append(result)

        if result.get("is_significant"):
            significant_set_ids.append(set_id)

    # --- Step 5: Assemble and save report ---
    # 보고서에는 twoway_anova 타입 제외한 세트만 전달 (per-set 결과와 병렬 매핑)
    report_analysis_sets = [s for s in analysis_sets if s.get("type") != "twoway_anova"]
    dashboard_md = assemble_dashboard(
        results=results,
        plots=plots,
        config=config,
        analysis_sets=report_analysis_sets,
        twoway_result=twoway_result,
    )

    output_path = _determine_output_path(config, excel_path)

    try:
        save_report(dashboard_md, output_path)
    except Exception as e:
        error_result = {"status": "error", "error": f"보고서 저장 오류: {e}"}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)

    # --- Step 6: Print JSON summary to stdout ---
    summary = {
        "status": "success",
        "report_path": output_path,
        "analysis_count": len(results),
        "significant_count": len(significant_set_ids),
        "significant_sets": significant_set_ids,
        "total_groups_found": len(
            {g for aset in analysis_sets for g in aset.get("groups", [])}
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
