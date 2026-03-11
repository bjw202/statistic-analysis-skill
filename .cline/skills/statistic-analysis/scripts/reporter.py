#!/usr/bin/env python3
"""Markdown dashboard assembly for statistical analysis."""

import base64
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


def png_to_base64(png_bytes: bytes) -> str:
    """
    Convert PNG bytes to a base64-encoded data URI for embedding in Markdown.

    Args:
        png_bytes: Raw PNG image data.

    Returns:
        Base64-encoded data URI string.
    """
    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _get_cohens_d_magnitude(d_abs: float) -> str:
    """Get Cohen's d magnitude label."""
    if d_abs < 0.2:
        return "무시 가능한 (negligible)"
    elif d_abs < 0.5:
        return "작은 (small)"
    elif d_abs < 0.8:
        return "중간 (medium)"
    else:
        return "큰 (large)"


def _layman_cohens_d(d_abs: float) -> str:
    """Plain-language description of Cohen's d for non-statisticians."""
    if d_abs < 0.2:
        return "두 그룹의 차이가 거의 없는 수준입니다."
    elif d_abs < 0.5:
        return "두 그룹 사이에 약간의 차이가 있지만, 실생활에서 느끼기 어려운 수준입니다."
    elif d_abs < 0.8:
        return "두 그룹 사이에 눈에 띄는 차이가 있습니다. 실험 조건이 결과에 어느 정도 영향을 준 것으로 보입니다."
    else:
        return "두 그룹 사이에 매우 뚜렷한 차이가 있습니다. 실험 조건이 결과에 큰 영향을 주었습니다."


def _layman_p_value(p_value: float, alpha: float, is_sig: bool) -> str:
    """Plain-language description of p-value for non-statisticians."""
    pct = p_value * 100
    if is_sig:
        return (
            f"이 결과가 단순한 우연일 확률은 {pct:.1f}%로, "
            f"기준값({alpha * 100:.0f}%)보다 낮습니다. "
            "즉, 관찰된 차이는 실제로 의미 있는 차이일 가능성이 높습니다."
        )
    else:
        return (
            f"이 결과가 단순한 우연일 확률은 {pct:.1f}%로, "
            f"기준값({alpha * 100:.0f}%)보다 높습니다. "
            "즉, 관찰된 차이가 우연에 의한 것일 가능성을 배제하기 어렵습니다."
        )


def _layman_test_name(test_name: str) -> str:
    """Plain-language explanation of the statistical test used."""
    explanations = {
        "independent_t_test": (
            "두 그룹의 평균을 비교하는 t-검정을 사용했습니다. "
            "두 그룹 모두 정규분포를 따르고 분산이 비슷할 때 사용합니다."
        ),
        "welchs_t_test": (
            "두 그룹의 평균을 비교하는 Welch t-검정을 사용했습니다. "
            "두 그룹의 분산이 다를 때도 안정적으로 작동하는 방법입니다."
        ),
        "mann_whitney_u": (
            "Mann-Whitney U 검정을 사용했습니다. "
            "데이터가 정규분포를 따르지 않을 때 사용하는 방법으로, "
            "평균 대신 순위(rank)를 비교합니다."
        ),
        "one_way_anova": (
            "세 그룹 이상의 평균을 한 번에 비교하는 분산분석(ANOVA)을 사용했습니다. "
            "모든 그룹이 정규분포를 따르고 분산이 비슷할 때 사용합니다."
        ),
        "welch_anova": (
            "그룹 간 분산이 다를 때 사용하는 Welch ANOVA를 사용했습니다. "
            "일반 ANOVA보다 더 안정적인 결과를 제공합니다."
        ),
        "kruskal_wallis": (
            "Kruskal-Wallis 검정을 사용했습니다. "
            "데이터가 정규분포를 따르지 않는 세 그룹 이상을 비교할 때 사용하는 방법으로, "
            "순위(rank)를 기반으로 분석합니다."
        ),
    }
    return explanations.get(test_name, "통계 검정을 사용하여 그룹 간 차이를 평가했습니다.")


def _get_eta_squared_magnitude(eta_sq: float) -> str:
    """Get eta-squared magnitude label."""
    if eta_sq < 0.01:
        return "무시 가능한"
    elif eta_sq < 0.06:
        return "작은"
    elif eta_sq < 0.14:
        return "중간"
    else:
        return "큰"


def build_descriptive_table(results: list[dict], config: dict) -> str:
    """
    Build a Markdown table summarizing descriptive statistics for all groups.

    Args:
        results: List of analysis result dicts.
        config: Analysis config dict.

    Returns:
        Markdown table string.
    """
    # Collect all groups across all results
    all_groups: dict[str, dict] = {}
    for result in results:
        for name, stats_dict in result.get("descriptive", {}).items():
            if name not in all_groups and stats_dict.get("n", 0) > 0:
                all_groups[name] = stats_dict

    if not all_groups:
        return "_기술 통계 없음_\n"

    lines = ["| 그룹 | N | 평균 | 표준편차 | 중앙값 | 최솟값 | 최댓값 |",
             "|------|---|------|----------|--------|--------|--------|"]

    for name, s in all_groups.items():
        if s.get("n", 0) == 0:
            continue
        lines.append(
            f"| {name} "
            f"| {s['n']} "
            f"| {s['mean']:.4f} "
            f"| {s['std']:.4f} "
            f"| {s['median']:.4f} "
            f"| {s['min']:.4f} "
            f"| {s['max']:.4f} |"
        )

    return "\n".join(lines) + "\n"


def build_interpretation(result: dict, analysis_set: dict, config: dict) -> str:
    """
    Build a 2-3 sentence natural language interpretation of a statistical result.

    Args:
        result: Analysis result dict from analysis_engine.run_analysis().
        analysis_set: Analysis set dict from annotator.build_analysis_sets().
        config: Full analysis config.

    Returns:
        Natural language interpretation string.
    """
    factor = analysis_set.get("isolates_factor") or "조건"
    description = config.get("experiment", {}).get("description", "측정값")
    groups = analysis_set.get("groups", [])
    is_sig = result.get("is_significant", False)
    p_value = result.get("test_result", {}).get("p_value")
    alpha = result.get("alpha", 0.05)
    cohens_d = result.get("cohens_d")
    eta_squared = result.get("eta_squared")
    test_display = result.get("test_display", "통계 검정")
    descriptive = result.get("descriptive", {})

    lines = []

    if is_sig:
        if len(groups) == 2 and len(groups) <= len(descriptive):
            g1, g2 = groups[0], groups[1]
            desc1 = descriptive.get(g1, {})
            desc2 = descriptive.get(g2, {})
            mean1 = desc1.get("mean")
            mean2 = desc2.get("mean")

            # Significance sentence
            if p_value is not None:
                lines.append(
                    f"**{g1}**와 **{g2}** 사이에 통계적으로 유의한 차이가 있었습니다 "
                    f"({test_display}: p = {p_value:.4f}, α = {alpha})."
                )
            else:
                lines.append(
                    f"**{g1}**와 **{g2}** 사이에 통계적으로 유의한 차이가 있었습니다."
                )

            # Direction sentence
            if mean1 is not None and mean2 is not None:
                diff = mean2 - mean1
                if diff > 0:
                    lines.append(
                        f"**{g2}**에서 {description}이 더 높았습니다 "
                        f"(Δ = +{diff:.4f}, {g1}: {mean1:.4f} → {g2}: {mean2:.4f})."
                    )
                elif diff < 0:
                    lines.append(
                        f"**{g2}**에서 {description}이 더 낮았습니다 "
                        f"(Δ = {diff:.4f}, {g1}: {mean1:.4f} → {g2}: {mean2:.4f})."
                    )
                else:
                    lines.append(f"두 그룹의 평균은 동일했습니다 ({mean1:.4f}).")
        else:
            # Multi-group
            if p_value is not None:
                n_groups = result.get("n_groups", len(groups))
                lines.append(
                    f"**{n_groups}개 그룹** 간에 통계적으로 유의한 차이가 있었습니다 "
                    f"({test_display}: p = {p_value:.4f}, α = {alpha})."
                )

    else:
        # Non-significant
        if p_value is not None:
            lines.append(
                f"통계적으로 유의한 차이가 발견되지 않았습니다 "
                f"({test_display}: p = {p_value:.4f}, α = {alpha})."
            )
        else:
            lines.append("통계적으로 유의한 차이가 발견되지 않았습니다.")

    # Effect size sentence
    effect_parts = []
    if cohens_d is not None:
        magnitude = _get_cohens_d_magnitude(abs(cohens_d))
        effect_parts.append(f"Cohen's d = {cohens_d:.3f} ({magnitude} 효과 크기)")
    if eta_squared is not None:
        magnitude = _get_eta_squared_magnitude(eta_squared)
        effect_parts.append(f"η² = {eta_squared:.3f} ({magnitude} 효과 크기)")

    if effect_parts:
        lines.append("효과 크기: " + ", ".join(effect_parts) + ".")

    # Factor context for factor isolation
    if analysis_set.get("type") == "factor_isolation" and factor != "조건":
        factor_values = analysis_set.get("factor_values", {})
        varying = factor_values.get("varying", {})
        held = factor_values.get("held_constant", {})

        if varying.get(factor) and isinstance(varying[factor], list) and len(varying[factor]) == 2:
            v1, v2 = varying[factor]
            context = f"(요인 **{factor}**: {v1} → {v2}"
            if held:
                held_str = ", ".join(f"{k}={v}" for k, v in held.items())
                context += f"; {held_str} 고정"
            context += ")"
            lines.append(context)

    # Sample size caveat
    min_n = min(
        (stats.get("n", 99) for stats in descriptive.values() if stats.get("n", 0) > 0),
        default=99
    )
    if min_n < 5:
        lines.append(
            f"⚠️ 주의: 최소 샘플 수 N={min_n}로 검정력이 낮을 수 있습니다."
        )

    technical = " ".join(lines)

    # --- 비전문가용 해석 (쉽게 말하면) ---
    plain_lines = []

    if p_value is not None:
        plain_lines.append(_layman_p_value(p_value, alpha, is_sig))

    if cohens_d is not None:
        plain_lines.append(_layman_cohens_d(abs(cohens_d)))

    if len(groups) == 2 and len(groups) <= len(descriptive):
        g1, g2 = groups[0], groups[1]
        desc1 = descriptive.get(g1, {})
        desc2 = descriptive.get(g2, {})
        mean1 = desc1.get("mean")
        mean2 = desc2.get("mean")
        n1 = desc1.get("n")
        n2 = desc2.get("n")
        if mean1 is not None and mean2 is not None:
            pct_diff = abs(mean2 - mean1) / mean1 * 100 if mean1 != 0 else 0
            direction = "낮았습니다" if mean2 < mean1 else "높았습니다"
            plain_lines.append(
                f"구체적으로, **{g1}** 그룹(N={n1}, 평균={mean1:.3f})에 비해 "
                f"**{g2}** 그룹(N={n2}, 평균={mean2:.3f})의 측정값이 "
                f"약 {pct_diff:.1f}% {direction}."
            )

    if min_n < 10:
        plain_lines.append(
            f"단, 각 그룹의 샘플 수가 적어(최소 N={min_n}) "
            "결과 해석 시 주의가 필요합니다."
        )

    layman_block = (
        "\n\n> **쉽게 말하면:**\n> "
        + "\n> ".join(plain_lines)
        if plain_lines else ""
    )

    return technical + layman_block


def build_analysis_section(result: dict, plot_bytes: bytes | None, config: dict, analysis_set: dict | None = None, index: int = 1) -> str:
    """
    Build a Markdown section for one analysis set.

    Args:
        result: Analysis result dict.
        plot_bytes: Optional PNG plot bytes.
        config: Analysis config.
        analysis_set: The analysis set dict.
        index: Section number for display.

    Returns:
        Markdown section string.
    """
    if result.get("error"):
        return f"## 분석 {index}: 오류\n\n오류: {result['error']}\n\n"

    test_display = result.get("test_display", "N/A")
    is_sig = result.get("is_significant", False)
    p_value = result.get("test_result", {}).get("p_value")
    alpha = result.get("alpha", 0.05)
    groups = result.get("groups_analyzed", [])

    label = ""
    if analysis_set:
        label = analysis_set.get("label", f"분석 {index}")
    else:
        label = " vs ".join(groups) if groups else f"분석 {index}"

    sig_str = "유의함 ✓" if is_sig else "유의하지 않음 ✗"
    p_str = f"{p_value:.4f}" if p_value is not None else "N/A"

    test_name = result.get("test_name", "")
    layman_test = _layman_test_name(test_name)

    lines = [
        f"## 분석 {index}: {label}",
        "",
        f"**검정 방법:** {test_display}",
        f"> 💡 *{layman_test}*",
        "",
        f"**결과:** {sig_str}",
        f"**p-값:** {p_str} (α = {alpha})",
    ]

    # Test statistic
    test_result = result.get("test_result", {})
    stat = test_result.get("stat")
    df_val = test_result.get("df")
    test_name = result.get("test_name", "")

    stat_labels = {
        "independent_t_test": "t",
        "welchs_t_test": "t",
        "mann_whitney_u": "U",
        "one_way_anova": "F",
        "welch_anova": "F",
        "kruskal_wallis": "H",
    }
    stat_label = stat_labels.get(test_name, "stat")

    if stat is not None:
        stat_str = f"**통계량:** {stat_label} = {stat:.4f}"
        if df_val is not None:
            stat_str += f" (df = {df_val})"
        lines.append(stat_str)

    # Effect sizes
    cohens_d = result.get("cohens_d")
    eta_sq = result.get("eta_squared")
    if cohens_d is not None:
        magnitude = _get_cohens_d_magnitude(abs(cohens_d))
        lines.append(f"**Cohen's d:** {cohens_d:.3f} ({magnitude})")
    if eta_sq is not None:
        magnitude = _get_eta_squared_magnitude(eta_sq)
        lines.append(f"**Eta-squared (η²):** {eta_sq:.3f} ({magnitude})")

    lines.append("")

    # Descriptive statistics table
    descriptive = result.get("descriptive", {})
    if descriptive:
        lines.append("### 기술 통계")
        lines.append("")
        lines.append("| 그룹 | N | 평균 | 표준편차 | 중앙값 |")
        lines.append("|------|---|------|----------|--------|")
        for name, s in descriptive.items():
            if s.get("n", 0) > 0:
                lines.append(
                    f"| {name} | {s['n']} | {s['mean']:.4f} "
                    f"| {s['std']:.4f} | {s['median']:.4f} |"
                )
        lines.append("")

    # Normality test results
    normality_results = result.get("normality_results", {})
    if normality_results:
        lines.append("### 정규성 검정 (Shapiro-Wilk)")
        lines.append("")
        lines.append("| 그룹 | N | W 통계량 | p-값 | 정규성 |")
        lines.append("|------|---|---------|------|--------|")
        for gname, nr in normality_results.items():
            stat_val = f"{nr['stat']:.4f}" if nr.get("stat") is not None else "N/A"
            p_v = f"{nr['p_value']:.4f}" if nr.get("p_value") is not None else "N/A"
            normal_str = "정규" if nr.get("is_normal") else "비정규"
            note = nr.get("note", "")
            if note:
                normal_str += f" ⚠️"
            lines.append(f"| {gname} | {nr.get('n', 0)} | {stat_val} | {p_v} | {normal_str} |")
        lines.append("")

    # Post-hoc results
    posthoc = result.get("posthoc_matrix")
    if posthoc is not None:
        lines.append("### 사후 검정 (Post-hoc)")
        lines.append("")
        try:
            if isinstance(posthoc, pd.DataFrame):
                lines.append(posthoc.to_markdown())
            else:
                lines.append(str(posthoc))
        except Exception:
            lines.append("_사후 검정 결과 표시 오류_")
        lines.append("")

    # Interpretation
    if analysis_set:
        interpretation = build_interpretation(result, analysis_set, config)
        lines.append("### 해석")
        lines.append("")
        lines.append(interpretation)
        lines.append("")

    # Plot
    if plot_bytes:
        b64 = png_to_base64(plot_bytes)
        lines.append("### 시각화")
        lines.append("")
        lines.append(f"![Box Plot]({b64})")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def assemble_dashboard(
    results: list[dict],
    plots: dict[str, bytes],
    config: dict,
    analysis_sets: list[dict] | None = None,
    twoway_result: dict | None = None,
) -> str:
    """
    완성된 마크다운 분석 대시보드를 조립합니다.

    요인 설계 분석이 있는 경우 요인 영향도 비교 섹션을
    요약 표 직후, 상세 결과 이전에 삽입합니다.

    Args:
        results: 분석 결과 딕셔너리 목록
        plots: analysis_set_id -> PNG bytes 매핑 딕셔너리
        config: 분석 설정 딕셔너리
        analysis_sets: 분석 세트 딕셔너리 목록 (results와 병렬)
        twoway_result: run_twoway_anova()의 결과 (없으면 None)

    Returns:
        완성된 마크다운 문자열
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    excel_file = config.get("experiment", {}).get("excel_file", "N/A")
    description = config.get("experiment", {}).get("description", "N/A")
    alpha = config.get("analysis", {}).get("alpha", 0.05)

    lines = [
        "# 통계 분석 보고서",
        "",
        f"**생성 시간:** {timestamp}",
        f"**데이터 파일:** {excel_file}",
        f"**실험 설명:** {description}",
        f"**유의수준:** α = {alpha}",
        "",
        "---",
        "",
        "## 분석 요약",
        "",
    ]

    # Summary table
    n_significant = sum(1 for r in results if r.get("is_significant", False))
    n_total = len(results)

    lines.append(f"**총 분석 수:** {n_total}개 | **유의한 비교:** {n_significant}개 | **유의하지 않은 비교:** {n_total - n_significant}개")
    lines.append("")
    lines.append("| # | 비교 | 검정 | p-값 | 유의함? | Cohen's d |")
    lines.append("|---|------|------|------|---------|-----------|")

    for i, result in enumerate(results, 1):
        if result.get("error"):
            lines.append(f"| {i} | 오류 | - | - | - | - |")
            continue

        aset = analysis_sets[i - 1] if analysis_sets and i <= len(analysis_sets) else None
        label = aset.get("label", f"분석 {i}") if aset else f"분석 {i}"
        # Truncate long labels
        if len(label) > 40:
            label = label[:38] + ".."

        test = result.get("test_display", "N/A")
        p_val = result.get("test_result", {}).get("p_value")
        p_str = f"{p_val:.4f}" if p_val is not None else "N/A"
        sig = "✓" if result.get("is_significant") else "✗"
        d = result.get("cohens_d")
        d_str = f"{d:.3f}" if d is not None else "-"

        lines.append(f"| {i} | {label} | {test} | {p_str} | {sig} | {d_str} |")

    lines.append("")

    # Significant comparisons summary
    sig_results = [
        (i, r) for i, r in enumerate(results, 1)
        if r.get("is_significant") and not r.get("error")
    ]
    if sig_results:
        lines.append("### 유의한 비교 목록")
        lines.append("")
        for idx, result in sig_results:
            aset = analysis_sets[idx - 1] if analysis_sets and idx <= len(analysis_sets) else None
            label = aset.get("label", f"분석 {idx}") if aset else f"분석 {idx}"
            p_val = result.get("test_result", {}).get("p_value")
            p_str = f"{p_val:.4f}" if p_val is not None else "N/A"
            lines.append(f"- **분석 {idx}:** {label} (p = {p_str})")
        lines.append("")

    # 요인 설계 분석 결과가 있으면 요약 직후 삽입
    if twoway_result is not None:
        factorial_section = build_factor_comparison_section(twoway_result, config)
        lines.append(factorial_section)
    else:
        lines.append("---")
        lines.append("")

    lines.append("## 상세 결과")
    lines.append("")

    # Individual analysis sections
    for i, result in enumerate(results, 1):
        aset = analysis_sets[i - 1] if analysis_sets and i <= len(analysis_sets) else None
        set_id = aset.get("id") if aset else None
        plot_bytes = plots.get(set_id) if set_id else None

        section = build_analysis_section(result, plot_bytes, config, aset, i)
        lines.append(section)

    # Footer
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*MoAI statistic-analysis skill에 의해 자동 생성됨*")
    lines.append("")

    return "\n".join(lines)


def _get_partial_eta_magnitude(eta: float) -> tuple[str, str]:
    """
    편 에타제곱 크기에 따른 레이블과 별점 등급을 반환합니다.

    Cohen(1988) 기준:
    - < 0.01: 무시 가능한 효과
    - 0.01~0.059: 작은 효과
    - 0.06~0.139: 중간 효과
    - >= 0.14: 큰 효과

    Args:
        eta: 편 에타제곱 값 (0~1)

    Returns:
        (크기 레이블, 별점 문자열) 튜플
    """
    if eta < 0.01:
        return ("무시 가능한", "")
    elif eta < 0.06:
        return ("작은 효과", "★")
    elif eta < 0.14:
        return ("중간 효과", "★★")
    else:
        return ("큰 효과", "★★★")


def _get_cohens_d_stars(d_abs: float) -> tuple[str, str]:
    """
    Cohen's d 절대값에 따른 레이블과 별점 등급을 반환합니다.

    Args:
        d_abs: Cohen's d 절대값

    Returns:
        (크기 레이블, 별점 문자열) 튜플
    """
    if d_abs < 0.2:
        return ("무시 가능한", "")
    elif d_abs < 0.5:
        return ("작은 효과", "★")
    elif d_abs < 0.8:
        return ("중간 효과", "★★")
    else:
        return ("큰 효과", "★★★")


def build_factor_comparison_section(twoway_result: dict, config: dict) -> str:
    """
    요인 영향도 비교 섹션을 마크다운으로 구성합니다.

    Two-Way ANOVA 결과(method='two_way_anova')와
    풀링된 요인 분리 비교 결과(method='factor_isolation_pooled') 모두 지원합니다.

    Args:
        twoway_result: run_twoway_anova() 또는 풀링 비교의 반환 딕셔너리
        config: 전체 분석 설정 딕셔너리

    Returns:
        마크다운 섹션 문자열
    """
    if twoway_result.get("error") and not twoway_result.get("factors"):
        return (
            f"## 요인 영향도 비교\n\n"
            f"> ⚠️ 분석 실행 중 오류가 발생했습니다: {twoway_result.get('error')}\n\n---\n\n"
        )

    factors = twoway_result.get("factors", {})
    method = twoway_result.get("method", "two_way_anova")
    alpha = config.get("analysis", {}).get("alpha", 0.05)

    is_pooled = method == "factor_isolation_pooled"

    if is_pooled:
        method_display = twoway_result.get("method_display", "요인 분리 풀링 비교")
        lines = [
            "## 요인 영향도 비교",
            "",
            f"**분석 방법:** {method_display}",
            "> 📊 *불완전 요인 설계로 인해 반복실험 데이터를 풀링하여 요인별 개별 비교를 수행했습니다.*",
            "",
            "| 요인 | 검정 | p-값 | Cohen's d | 영향도 |",
            "|------|------|------|-----------|--------|",
        ]
    else:
        normality_ok = twoway_result.get("normality_ok", True)
        method_label = "이원 분산분석" if method == "two_way_anova" else "비모수 이원 분석 (순위 변환)"
        lines = [
            "## 요인 영향도 비교 (Two-Way ANOVA)",
            "",
            f"**분석 방법:** {method_label}",
        ]
        if not normality_ok:
            lines.append("> 📊 *잔차 정규성 불충족으로 Aligned Rank Transform 방법을 적용했습니다.*")
        lines.append("")
        lines.append("| 요인 | F | p-값 | 편 η² | 영향도 |")
        lines.append("|------|---|------|-------|--------|")

    factor_ranking = twoway_result.get("factor_ranking", [])

    if is_pooled:
        # factor_ranking은 딕셔너리 리스트: {factor, cohens_d, p_value, is_significant, test_display}
        for fr in factor_ranking:
            factor_name = fr.get("factor", "unknown")
            d_val = fr.get("cohens_d", 0.0)
            p_val = fr.get("p_value")
            is_sig = fr.get("is_significant", False)
            test_display = fr.get("test_display", "N/A")

            p_str = "<0.001" if (p_val is not None and p_val < 0.001) else (
                f"{p_val:.4f}" if p_val is not None else "N/A"
            )
            d_str = f"{d_val:.3f}"

            magnitude_label, stars = _get_cohens_d_stars(d_val)
            if is_sig:
                influence_str = f"{stars} {magnitude_label}" if stars else magnitude_label
            else:
                influence_str = "유의하지 않음"

            lines.append(f"| {factor_name} | {test_display} | {p_str} | {d_str} | {influence_str} |")
    else:
        # factor_ranking은 튜플 리스트: (factor_name, eta_sq)
        for factor_name, eta_sq in factor_ranking:
            factor_info = factors.get(factor_name, {})
            f_val = factor_info.get("F")
            p_val = factor_info.get("p_value")
            is_sig = factor_info.get("is_significant", False)

            f_str = f"{f_val:.2f}" if f_val is not None else "N/A"
            p_str = "<0.001" if (p_val is not None and p_val < 0.001) else (
                f"{p_val:.3f}" if p_val is not None else "N/A"
            )

            magnitude_label, stars = _get_partial_eta_magnitude(eta_sq)
            eta_str = f"{eta_sq:.3f}"

            if is_sig:
                influence_str = f"{stars} {magnitude_label}" if stars else magnitude_label
            else:
                influence_str = "유의하지 않음"

            lines.append(f"| {factor_name} | {f_str} | {p_str} | {eta_str} | {influence_str} |")

        # 교호작용 행 추가 (Two-Way ANOVA에만 해당)
        interaction_info = factors.get("interaction", {})
        if interaction_info:
            f_int = interaction_info.get("F")
            p_int = interaction_info.get("p_value")
            eta_int = interaction_info.get("eta_sq_partial", 0.0)
            is_sig_int = interaction_info.get("is_significant", False)

            f_str = f"{f_int:.2f}" if f_int is not None else "N/A"
            p_str = "<0.001" if (p_int is not None and p_int < 0.001) else (
                f"{p_int:.3f}" if p_int is not None else "N/A"
            )
            eta_str = f"{eta_int:.3f}"

            if is_sig_int:
                magnitude_label, stars = _get_partial_eta_magnitude(eta_int)
                influence_str = f"{stars} {magnitude_label}" if stars else magnitude_label
            else:
                influence_str = "유의하지 않음"

            lines.append(f"| 교호작용 | {f_str} | {p_str} | {eta_str} | {influence_str} |")

    lines.append("")

    # 결론 문장 추가
    conclusion = build_factorial_conclusion(twoway_result, config)
    if conclusion:
        lines.append("### 요인 영향도 결론")
        lines.append("")
        lines.append(conclusion)
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def build_factorial_conclusion(twoway_result: dict, config: dict) -> str:
    """
    요인 영향도 분석 결과를 자연어 결론 문장으로 요약합니다.

    Two-Way ANOVA(편 η² 기반) 및 풀링된 요인 분리 비교(Cohen's d 기반) 모두 지원합니다.

    Args:
        twoway_result: run_twoway_anova() 또는 풀링 비교의 반환 딕셔너리
        config: 전체 분석 설정 딕셔너리

    Returns:
        결론 문자열 (마크다운 인라인 형식)
    """
    factors = twoway_result.get("factors", {})
    factor_ranking = twoway_result.get("factor_ranking", [])
    description = config.get("experiment", {}).get("description", "측정값")
    alpha = config.get("analysis", {}).get("alpha", 0.05)
    method = twoway_result.get("method", "two_way_anova")
    is_pooled = method == "factor_isolation_pooled"

    if not factor_ranking:
        return ""

    # 형식 통일: 유의한 요인 추출
    if is_pooled:
        # factor_ranking = [{factor, cohens_d, p_value, is_significant, ...}, ...]
        sig_factors = [
            fr for fr in factor_ranking if fr.get("is_significant", False)
        ]
        all_factors = factor_ranking
    else:
        # factor_ranking = [(name, eta_sq), ...]
        sig_factors = [
            (name, eta)
            for name, eta in factor_ranking
            if factors.get(name, {}).get("is_significant", False)
        ]
        all_factors = factor_ranking

    conclusion_parts = []

    if is_pooled:
        # --- 풀링된 요인 분리 비교 결론 ---
        if len(sig_factors) == 0:
            conclusion_parts.append(
                f"분석 결과, 어떤 요인도 **{description}**에 통계적으로 유의한 영향을 미치지 않았습니다 (α = {alpha})."
            )
        elif len(sig_factors) == 1:
            fr = sig_factors[0]
            name = fr["factor"]
            d_val = fr["cohens_d"]
            magnitude_label, _ = _get_cohens_d_stars(d_val)
            conclusion_parts.append(
                f"**{name}**(Cohen's d={d_val:.3f}, {magnitude_label})만이 "
                f"**{description}**에 통계적으로 유의한 영향을 미쳤습니다."
            )
            nonsig = [f["factor"] for f in all_factors if not f.get("is_significant", False)]
            if nonsig:
                nonsig_str = ", ".join(f"**{n}**" for n in nonsig)
                conclusion_parts.append(
                    f"{nonsig_str}의 영향은 통계적으로 유의하지 않았습니다."
                )
        else:
            # 2개 이상 유의한 요인
            top = sig_factors[0]
            second = sig_factors[1]
            top_name, top_d = top["factor"], top["cohens_d"]
            second_name, second_d = second["factor"], second["cohens_d"]

            if second_d > 0:
                ratio = top_d / second_d
                ratio_str = f"약 {ratio:.1f}배"
            else:
                ratio_str = "훨씬"

            conclusion_parts.append(
                f"**{top_name}**(Cohen's d={top_d:.3f})이 "
                f"**{second_name}**(Cohen's d={second_d:.3f})보다 "
                f"**{description}**에 {ratio_str} 더 큰 영향을 미칩니다."
            )

            all_sig_str = " 및 ".join(f"**{f['factor']}**" for f in sig_factors)
            conclusion_parts.append(
                f"{all_sig_str} 모두 통계적으로 유의합니다 (p < {alpha})."
            )

        # 풀링 비교에서는 교호작용을 직접 분석할 수 없음을 안내
        conclusion_parts.append(
            "불완전 요인 설계로 인해 교호작용은 분석하지 않았습니다."
        )
    else:
        # --- Two-Way ANOVA 결론 ---
        interaction_info = factors.get("interaction", {})
        is_interaction_sig = interaction_info.get("is_significant", False)
        p_interaction = interaction_info.get("p_value")

        if len(sig_factors) == 0:
            conclusion_parts.append(
                f"분석 결과, 어떤 요인도 **{description}**에 통계적으로 유의한 영향을 미치지 않았습니다 (α = {alpha})."
            )
        elif len(sig_factors) == 1:
            name, eta = sig_factors[0]
            magnitude_label, _ = _get_partial_eta_magnitude(eta)
            conclusion_parts.append(
                f"**{name}**(편 η²={eta:.3f}, {magnitude_label})만이 "
                f"**{description}**에 통계적으로 유의한 영향을 미쳤습니다."
            )
            nonsig = [name2 for name2, _ in factor_ranking if name2 not in [n for n, _ in sig_factors]]
            if nonsig:
                nonsig_str = ", ".join(f"**{n}**" for n in nonsig)
                conclusion_parts.append(
                    f"{nonsig_str}의 영향은 통계적으로 유의하지 않았습니다."
                )
        else:
            top_name, top_eta = sig_factors[0]
            second_name, second_eta = sig_factors[1]
            top_magnitude, _ = _get_partial_eta_magnitude(top_eta)

            if second_eta > 0:
                ratio = top_eta / second_eta
                ratio_str = f"약 {ratio:.1f}배"
            else:
                ratio_str = "훨씬"

            conclusion_parts.append(
                f"**{top_name}**(편 η²={top_eta:.3f})이 "
                f"**{second_name}**(편 η²={second_eta:.3f})보다 "
                f"**{description}**에 {ratio_str} 더 큰 영향을 미칩니다."
            )

            all_sig_str = " 및 ".join(f"**{n}**" for n, _ in sig_factors)
            conclusion_parts.append(
                f"{all_sig_str} 모두 통계적으로 유의합니다 (p < {alpha})."
            )

        # 교호작용 언급
        if is_interaction_sig and p_interaction is not None:
            p_str = "<0.001" if p_interaction < 0.001 else f"p={p_interaction:.3f}"
            conclusion_parts.append(
                f"⚠️ **교호작용**이 유의하여({p_str}), 두 요인의 효과가 독립적이지 않습니다. "
                "각 요인의 효과는 다른 요인의 수준에 따라 달라질 수 있습니다."
            )
        elif not is_interaction_sig and interaction_info:
            p_int_val = interaction_info.get("p_value")
            p_str = f"p={p_int_val:.3f}" if p_int_val is not None else ""
            conclusion_parts.append(
                f"교호작용은 통계적으로 유의하지 않아{('(' + p_str + ')') if p_str else ''}, "
                "두 요인의 효과는 독립적으로 작용합니다."
            )

    return " ".join(conclusion_parts)


def save_report(markdown: str, output_path: str) -> None:
    """
    Save the Markdown report to a file.

    Args:
        markdown: The complete Markdown content.
        output_path: Full path for the output file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)


if __name__ == "__main__":
    print("reporter.py — Markdown 보고서 조립 모듈")
    print("사용법: statistic_analyzer.py를 통해 실행하세요.")
