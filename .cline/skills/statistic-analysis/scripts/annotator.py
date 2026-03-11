#!/usr/bin/env python3
"""Analysis set auto-construction from annotated column config."""

import json
import os
from typing import Any


def detect_replicates(columns: dict) -> dict:
    """
    동일한 요인 조합을 가진 열(반복 측정)을 감지합니다.

    제어(control) 열을 제외한 처리(treatment) 열들 중 동일한 요인 조합을 가진
    열들을 묶어 반복 그룹을 반환합니다.

    Args:
        columns: config의 columns 딕셔너리

    Returns:
        요인 조합(frozenset) -> 열 이름 목록 딕셔너리.
        예: {frozenset({('광학계','개선'),('에칭량','6')}): ['Cond.1', 'Cond.2']}
    """
    # 처리(treatment) 열만 대상 (control 제외)
    treatment_cols = {
        name: info
        for name, info in columns.items()
        if info.get("role") != "control" and not info.get("is_control", False)
    }

    # 요인 조합별로 열 이름 그룹화
    groups: dict[frozenset, list[str]] = {}
    for col_name, col_info in treatment_cols.items():
        factors = col_info.get("factors", {})
        # 요인 조합을 frozenset으로 변환 (순서 무관 비교)
        factor_key = frozenset(factors.items())
        if factor_key not in groups:
            groups[factor_key] = []
        groups[factor_key].append(col_name)

    # 반복이 있는 그룹만 반환 (열이 2개 이상인 경우)
    return {k: v for k, v in groups.items() if len(v) >= 2}


def detect_factorial_design(columns: dict) -> dict | None:
    """
    열 요인 어노테이션으로부터 요인 설계(factorial design)를 자동 감지합니다.

    control 포함 모든 열의 요인 이름과 수준을 수집하여, 2개 이상의 요인 각각이
    2개 이상의 수준을 가진 경우 요인 설계로 판정합니다.

    Args:
        columns: config의 columns 딕셔너리

    Returns:
        요인 설계가 아니면 None.
        요인 설계이면 다음 딕셔너리:
        {
            "factors": {"광학계": ["기존", "개선"], "에칭량": ["6", "16"]},
            "design_label": "2×2",
            "is_balanced": True/False
        }
    """
    # 모든 열(control 포함)에서 요인 이름과 수준 수집
    factor_levels: dict[str, set[str]] = {}
    for col_name, col_info in columns.items():
        factors = col_info.get("factors", {})
        for factor_name, factor_value in factors.items():
            if factor_name not in factor_levels:
                factor_levels[factor_name] = set()
            factor_levels[factor_name].add(str(factor_value))

    # 2개 이상의 수준을 가진 요인만 추출
    multi_level_factors = {
        name: sorted(levels)
        for name, levels in factor_levels.items()
        if len(levels) >= 2
    }

    # 2개 이상의 요인이 있어야 요인 설계
    if len(multi_level_factors) < 2:
        return None

    # 설계 레이블 생성 (예: "2×2×3")
    level_counts = [len(levels) for levels in multi_level_factors.values()]
    design_label = "×".join(str(n) for n in level_counts)

    # 균형 설계 여부 확인
    # 각 요인 조합에 동일한 수의 열이 있으면 균형 설계
    all_combinations_count: dict[tuple, int] = {}
    for col_name, col_info in columns.items():
        factors = col_info.get("factors", {})
        # 대상 요인만 포함한 조합 키 생성
        key = tuple(
            factors.get(f, None)
            for f in sorted(multi_level_factors.keys())
        )
        all_combinations_count[key] = all_combinations_count.get(key, 0) + 1

    counts = list(all_combinations_count.values())
    is_balanced = len(set(counts)) == 1 if counts else False

    # 완전 설계 여부: 모든 요인 조합에 데이터가 있는지 확인
    expected_combinations = 1
    for levels in multi_level_factors.values():
        expected_combinations *= len(levels)
    is_complete = len(all_combinations_count) >= expected_combinations

    return {
        "factors": multi_level_factors,
        "design_label": design_label,
        "is_balanced": is_balanced,
        "is_complete": is_complete,
    }


def build_factorial_analysis_sets(columns: dict, replicates: dict) -> list[dict]:
    """
    요인 분산분석(two-way ANOVA)용 분석 세트를 구성합니다.

    모든 열(control 포함)을 하나의 "twoway_anova" 타입 분석 세트로 묶습니다.
    반복 측정 열들은 동일 요인 조합 그룹으로 풀링됩니다.

    Args:
        columns: config의 columns 딕셔너리
        replicates: detect_replicates()의 반환값

    Returns:
        twoway_anova 타입 분석 세트를 포함한 리스트
    """
    factorial_info = detect_factorial_design(columns)
    if factorial_info is None:
        return []

    # 모든 열 이름 수집
    all_col_names = list(columns.keys())

    # 요인 정보 구성
    factor_info = factorial_info["factors"]

    set_id = "twoway_anova_full"
    label = f"요인 설계 분석 ({factorial_info['design_label']})"

    return [{
        "id": set_id,
        "type": "twoway_anova",
        "groups": all_col_names,
        "label": label,
        "isolates_factor": None,
        "factor_values": {"varying": {}, "held_constant": {}},
        "factor_info": factor_info,
        "design_label": factorial_info["design_label"],
        "is_balanced": factorial_info["is_balanced"],
    }]


def build_factor_impact_pooled_sets(columns: dict, replicates: dict) -> list[dict]:
    """
    반복실험 풀링 + 요인 분리 비교 분석 세트를 구성합니다.

    불완전 요인 설계에서도 동작합니다. 각 요인에 대해 해당 요인만 다르고
    나머지 요인은 동일한 두 그룹을 찾아, 반복실험 데이터를 풀링하여 비교합니다.

    Args:
        columns: config의 columns 딕셔너리
        replicates: detect_replicates()의 반환값

    Returns:
        factor_impact_pooled 타입 분석 세트 리스트
    """
    factorial_info = detect_factorial_design(columns)
    if factorial_info is None:
        return []

    factor_names = list(factorial_info["factors"].keys())

    # 모든 열의 요인 값 매핑 (control 포함)
    col_factors: dict[str, dict[str, str]] = {}
    for col_name, col_info in columns.items():
        col_factors[col_name] = col_info.get("factors", {})

    # 반복실험 풀링 맵: 요인조합 -> [열이름들]
    # replicates는 treatment만 포함하므로, control도 추가
    pool_map: dict[frozenset, list[str]] = {}
    for col_name, col_info in columns.items():
        factors = col_info.get("factors", {})
        key = frozenset(factors.items())
        if key not in pool_map:
            pool_map[key] = []
        pool_map[key].append(col_name)

    analysis_sets = []

    for target_factor in factor_names:
        other_factors = [f for f in factor_names if f != target_factor]
        target_levels = factorial_info["factors"][target_factor]

        if len(target_levels) < 2:
            continue

        # 다른 요인의 고정값을 찾아서, target_factor만 다른 그룹 쌍 구성
        # 가능한 고정 조합들 수집
        fixed_combos: dict[tuple, dict[str, list[str]]] = {}
        for factor_key, col_list in pool_map.items():
            factor_dict = dict(factor_key)
            target_val = factor_dict.get(target_factor)
            if target_val is None:
                continue

            # 다른 요인들의 고정값 키
            fixed_key = tuple(
                factor_dict.get(f, "")
                for f in sorted(other_factors)
            )

            if fixed_key not in fixed_combos:
                fixed_combos[fixed_key] = {}
            if target_val not in fixed_combos[fixed_key]:
                fixed_combos[fixed_key][target_val] = []
            fixed_combos[fixed_key][target_val].extend(col_list)

        # 각 고정 조합에서 target_factor 수준이 2개 이상인 것 찾기
        for fixed_key, level_groups in fixed_combos.items():
            if len(level_groups) < 2:
                continue

            # 수준 쌍 비교 (보통 2개)
            levels = sorted(level_groups.keys())
            for i, lev_a in enumerate(levels):
                for lev_b in levels[i + 1:]:
                    cols_a = level_groups[lev_a]
                    cols_b = level_groups[lev_b]

                    held_constant = {
                        f: val
                        for f, val in zip(sorted(other_factors), fixed_key)
                        if val
                    }
                    held_str = ", ".join(f"{k}={v}" for k, v in held_constant.items())

                    set_id = (
                        f"factor_impact_{target_factor}_{lev_a}_vs_{lev_b}"
                        .replace(".", "_").replace(" ", "_").replace("/", "_")
                    )
                    label = (
                        f"{target_factor} 효과: {lev_a} vs {lev_b}"
                        + (f" ({held_str} 고정)" if held_str else "")
                    )

                    analysis_sets.append({
                        "id": set_id,
                        "type": "factor_impact_pooled",
                        "isolates_factor": target_factor,
                        "group_a": {
                            "columns": cols_a,
                            "label": lev_a,
                            "factor_value": lev_a,
                        },
                        "group_b": {
                            "columns": cols_b,
                            "label": lev_b,
                            "factor_value": lev_b,
                        },
                        "held_constant": held_constant,
                        "label": label,
                        "groups": cols_a + cols_b,
                        "factor_values": {
                            "varying": {target_factor: [lev_a, lev_b]},
                            "held_constant": held_constant,
                        },
                    })
                    break  # 한 고정 조합 당 하나의 비교만
            break  # 가장 좋은 고정 조합 하나만 사용

    return analysis_sets


def build_analysis_sets(config: dict) -> list[dict]:
    """
    Auto-construct analysis sets from the annotated column configuration.

    Dispatches to the appropriate builder based on analysis.intent:
      - "pairwise_vs_control": each treatment vs control
      - "factor_isolation": pairs differing in exactly 1 factor
      - "full_factorial": all pairwise combinations
      - "custom": uses pre-specified comparisons from config
      - "factor_impact_comparison": factorial design analysis

    Args:
        config: Full analysis config dict (see SKILL.md schema).

    Returns:
        List of analysis set dicts.
    """
    intent = config.get("analysis", {}).get("primary_goal", config.get("analysis", {}).get("intent", "pairwise_vs_control"))
    columns = config.get("columns", {})

    if intent == "factor_impact_comparison":
        replicates = detect_replicates(columns)
        factorial_info = detect_factorial_design(columns)

        if factorial_info and factorial_info.get("is_complete"):
            # 완전 설계: Two-Way ANOVA 사용
            return build_factorial_analysis_sets(columns, replicates)
        else:
            # 불완전 설계: 풀링된 요인 분리 비교 사용
            return build_factor_impact_pooled_sets(columns, replicates)
    elif intent == "pairwise_vs_control":
        return _pairwise_vs_control(columns)
    elif intent == "factor_isolation":
        return _factor_isolated_pairs(columns)
    elif intent == "full_factorial":
        return _full_factorial(columns)
    elif intent == "custom":
        return _custom_comparisons(config)
    else:
        # Default: pairwise vs control
        return _pairwise_vs_control(columns)


def _pairwise_vs_control(columns: dict) -> list[dict]:
    """
    Build analysis sets comparing each treatment column to the control.

    Args:
        columns: columns dict from config.

    Returns:
        List of analysis sets, one per treatment column.
    """
    control_col = None
    treatment_cols = []

    for col_name, col_info in columns.items():
        if col_info.get("role") == "control" or col_info.get("is_control", False):
            control_col = col_name
        else:
            treatment_cols.append(col_name)

    if control_col is None:
        return []

    analysis_sets = []
    for treat_col in treatment_cols:
        col_info = columns[treat_col]
        label = col_info.get("label", treat_col)
        factors = col_info.get("factors", {})
        factor_str = ", ".join(f"{k}={v}" for k, v in factors.items()) if factors else ""

        set_id = f"pairwise_{control_col}_vs_{treat_col}".replace(".", "_").replace(" ", "_")

        analysis_sets.append({
            "id": set_id,
            "type": "pairwise_vs_control",
            "groups": [control_col, treat_col],
            "label": f"{control_col} vs {treat_col}" + (f" ({factor_str})" if factor_str else ""),
            "isolates_factor": None,
            "factor_values": {
                "varying": factors,
                "held_constant": {},
            },
        })

    return analysis_sets


def _factor_isolated_pairs(columns: dict) -> list[dict]:
    """
    Build analysis sets for pairs of columns differing in exactly one factor.

    For each pair (c1, c2) of non-control columns, check if they differ in
    exactly one factor. If so, create an analysis set for that factor isolation.

    Algorithm:
        for each factor F in all_factors:
            for each pair (c1, c2) of treatment columns:
                differing = {k for k in all_factors if c1_factors.get(k) != c2_factors.get(k)}
                if len(differing) == 1 and F in differing:
                    # valid isolation pair

    Args:
        columns: columns dict from config.

    Returns:
        List of analysis sets for factor-isolated pairs.
    """
    treatment_cols = {
        name: info
        for name, info in columns.items()
        if info.get("role") != "control" and not info.get("is_control", False)
    }

    # Collect all factor names across all treatment columns
    all_factors: set[str] = set()
    for col_info in treatment_cols.values():
        all_factors.update(col_info.get("factors", {}).keys())

    analysis_sets = []
    seen_pairs: set[frozenset] = set()

    col_names = list(treatment_cols.keys())

    for factor_f in all_factors:
        for i, c1 in enumerate(col_names):
            for c2 in col_names[i + 1:]:
                pair_key = frozenset([c1, c2])
                if pair_key in seen_pairs:
                    continue

                c1_factors = treatment_cols[c1].get("factors", {})
                c2_factors = treatment_cols[c2].get("factors", {})

                # Find differing factors
                differing = {
                    k for k in all_factors
                    if c1_factors.get(k) != c2_factors.get(k)
                }

                if len(differing) == 1 and factor_f in differing:
                    seen_pairs.add(pair_key)

                    # Held constant: factors that are the same in both
                    held_constant = {
                        k: c1_factors.get(k, c2_factors.get(k))
                        for k in all_factors
                        if k not in differing
                        and (c1_factors.get(k) is not None or c2_factors.get(k) is not None)
                    }

                    # Remove None values
                    held_constant = {k: v for k, v in held_constant.items() if v is not None}

                    c1_val = c1_factors.get(factor_f, "unknown")
                    c2_val = c2_factors.get(factor_f, "unknown")

                    held_str = ", ".join(f"{k}={v}" for k, v in held_constant.items())
                    label = (
                        f"Effect of {factor_f}: {c1_val} vs {c2_val}"
                        + (f" ({held_str} fixed)" if held_str else "")
                    )

                    set_id = (
                        f"isolate_{factor_f}_{c1}_vs_{c2}"
                        .replace(".", "_").replace(" ", "_").replace("/", "_")
                    )

                    analysis_sets.append({
                        "id": set_id,
                        "type": "factor_isolation",
                        "groups": [c1, c2],
                        "label": label,
                        "isolates_factor": factor_f,
                        "factor_values": {
                            "varying": {factor_f: [c1_val, c2_val]},
                            "held_constant": held_constant,
                        },
                    })

    return analysis_sets


def _group_by_factor_level(columns: dict) -> list[dict]:
    """
    Pool columns that share the same factor=value combination.

    Groups columns by each unique factor=value, creating multi-group
    analysis sets for each factor.

    Args:
        columns: columns dict from config.

    Returns:
        List of analysis sets for grouped factor levels.
    """
    treatment_cols = {
        name: info
        for name, info in columns.items()
        if info.get("role") != "control" and not info.get("is_control", False)
    }

    control_cols = [
        name for name, info in columns.items()
        if info.get("role") == "control" or info.get("is_control", False)
    ]

    # Collect all factor names
    all_factors: set[str] = set()
    for col_info in treatment_cols.values():
        all_factors.update(col_info.get("factors", {}).keys())

    analysis_sets = []

    for factor_f in all_factors:
        # Group by factor value
        groups_by_value: dict[str, list[str]] = {}
        for col_name, col_info in treatment_cols.items():
            val = col_info.get("factors", {}).get(factor_f)
            if val is not None:
                if val not in groups_by_value:
                    groups_by_value[val] = []
                groups_by_value[val].append(col_name)

        if len(groups_by_value) < 2:
            continue

        # Include control if present
        all_group_columns = control_cols + [
            col
            for cols in groups_by_value.values()
            for col in cols
        ]

        set_id = f"group_aggregate_{factor_f}".replace(".", "_").replace(" ", "_")
        label = f"Factor {factor_f}: aggregated group comparison"

        analysis_sets.append({
            "id": set_id,
            "type": "group_aggregate",
            "groups": all_group_columns,
            "label": label,
            "isolates_factor": factor_f,
            "factor_values": {
                "varying": {factor_f: list(groups_by_value.keys())},
                "held_constant": {},
            },
        })

    return analysis_sets


def _full_factorial(columns: dict) -> list[dict]:
    """
    Build all pairwise comparison analysis sets.

    Args:
        columns: columns dict from config.

    Returns:
        List of all pairwise comparison analysis sets.
    """
    col_names = list(columns.keys())
    analysis_sets = []

    for i, c1 in enumerate(col_names):
        for c2 in col_names[i + 1:]:
            set_id = (
                f"pairwise_{c1}_vs_{c2}"
                .replace(".", "_").replace(" ", "_")
            )
            analysis_sets.append({
                "id": set_id,
                "type": "full_factorial",
                "groups": [c1, c2],
                "label": f"{c1} vs {c2}",
                "isolates_factor": None,
                "factor_values": {"varying": {}, "held_constant": {}},
            })

    return analysis_sets


def _custom_comparisons(config: dict) -> list[dict]:
    """
    Build analysis sets from explicit custom comparisons in config.

    Expects config["analysis"]["custom_comparisons"] to be a list of
    [col_a, col_b] pairs.

    Args:
        config: Full analysis config.

    Returns:
        List of custom analysis sets.
    """
    custom_pairs = config.get("analysis", {}).get("custom_comparisons", [])
    analysis_sets = []

    for i, pair in enumerate(custom_pairs):
        if len(pair) < 2:
            continue
        c1, c2 = str(pair[0]), str(pair[1])
        set_id = f"custom_{i + 1}_{c1}_vs_{c2}".replace(".", "_").replace(" ", "_")
        analysis_sets.append({
            "id": set_id,
            "type": "custom",
            "groups": [c1, c2],
            "label": f"{c1} vs {c2} (custom)",
            "isolates_factor": None,
            "factor_values": {"varying": {}, "held_constant": {}},
        })

    return analysis_sets


def save_config(config: dict, output_path: str) -> None:
    """
    Save the analysis config to a JSON file.

    Args:
        config: Config dict to save.
        output_path: Path for the output JSON file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    except Exception:
        pass  # Directory may already exist

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_config(config_path: str) -> dict:
    """
    Load an analysis config from a JSON file.

    Args:
        config_path: Path to the JSON config file.

    Returns:
        Config dict.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    """CLI utility for testing annotator functions."""
    import argparse

    parser = argparse.ArgumentParser(description="Analysis set builder — annotator")
    parser.add_argument("config_path", help="Path to analysis_config.json")
    args = parser.parse_args()

    try:
        config = load_config(args.config_path)
    except FileNotFoundError as e:
        print(f"오류: {e}")
        import sys
        sys.exit(1)

    analysis_sets = build_analysis_sets(config)
    print(f"생성된 분석 세트 수: {len(analysis_sets)}")
    for i, aset in enumerate(analysis_sets, 1):
        print(f"\n[{i}] {aset['label']}")
        print(f"    ID: {aset['id']}")
        print(f"    타입: {aset['type']}")
        print(f"    그룹: {aset['groups']}")


if __name__ == "__main__":
    main()
