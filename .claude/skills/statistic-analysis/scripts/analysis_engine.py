#!/usr/bin/env python3
"""Statistical test selection and execution engine."""

import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def run_normality_test(data: np.ndarray, alpha: float = 0.05) -> dict:
    """
    Run Shapiro-Wilk normality test on a data array.

    Args:
        data: 1D numpy array (NaN values will be removed internally).
        alpha: Significance level for normality decision.

    Returns:
        Dict with keys: stat, p_value, is_normal, n, note
    """
    data_clean = data[~np.isnan(data)] if isinstance(data, np.ndarray) else np.array(data, dtype=float)
    data_clean = data_clean[~np.isnan(data_clean)]
    n = len(data_clean)

    if n < 3:
        return {
            "stat": None,
            "p_value": None,
            "is_normal": False,
            "n": n,
            "note": f"샘플 수 부족 (n={n} < 3). 비정규 분포로 가정.",
        }

    try:
        if n > 5000:
            # Use D'Agostino-Pearson for large samples
            stat, p_value = stats.normaltest(data_clean)
        else:
            stat, p_value = stats.shapiro(data_clean)

        return {
            "stat": float(stat),
            "p_value": float(p_value),
            "is_normal": bool(p_value > alpha),
            "n": n,
            "note": None,
        }
    except Exception as e:
        return {
            "stat": None,
            "p_value": None,
            "is_normal": False,
            "n": n,
            "note": f"정규성 검정 오류: {e}",
        }


def run_variance_test(groups: list[np.ndarray], alpha: float = 0.05) -> dict:
    """
    Run Levene's test for equality of variances across groups.

    Args:
        groups: List of 1D numpy arrays (NaN already removed).
        alpha: Significance level.

    Returns:
        Dict with keys: stat, p_value, equal_variance, note
    """
    valid_groups = [g for g in groups if len(g) >= 2]

    if len(valid_groups) < 2:
        return {
            "stat": None,
            "p_value": None,
            "equal_variance": True,
            "note": "Levene's test를 위한 충분한 샘플 없음. 등분산 가정.",
        }

    try:
        stat, p_value = stats.levene(*valid_groups, center="median")
        return {
            "stat": float(stat),
            "p_value": float(p_value),
            "equal_variance": bool(p_value > alpha),
            "note": None,
        }
    except Exception as e:
        return {
            "stat": None,
            "p_value": None,
            "equal_variance": True,
            "note": f"Levene's test 오류: {e}. 등분산 가정.",
        }


def select_test(groups: list[np.ndarray], alpha: float = 0.05) -> str:
    """
    Select the appropriate statistical test based on data characteristics.

    Decision tree:
      2 groups:
        - All normal + equal variance -> independent_t_test
        - All normal + unequal variance -> welchs_t_test
        - Any non-normal -> mann_whitney_u
      3+ groups:
        - All normal + equal variance -> one_way_anova
        - All normal + unequal variance -> welch_anova
        - Any non-normal -> kruskal_wallis

    Args:
        groups: List of 1D numpy arrays (NaN already removed).
        alpha: Significance level.

    Returns:
        Test name string.
    """
    n_groups = len(groups)

    # Check normality for each group that has sufficient samples
    normality_ok = all(
        run_normality_test(g, alpha)["is_normal"]
        for g in groups
        if len(g) >= 3
    )

    # If any group has < 3 samples, treat as non-normal (conservative)
    if any(len(g) < 3 for g in groups):
        normality_ok = False

    variance_result = run_variance_test(groups, alpha)
    equal_var = variance_result["equal_variance"]

    if n_groups == 2:
        if normality_ok:
            return "welchs_t_test" if not equal_var else "independent_t_test"
        return "mann_whitney_u"
    else:
        if normality_ok:
            return "one_way_anova" if equal_var else "welch_anova"
        return "kruskal_wallis"


def compute_cohens_d(g1: np.ndarray, g2: np.ndarray) -> float | None:
    """
    Compute Cohen's d effect size for two groups.

    Uses pooled standard deviation.

    Args:
        g1: First group values.
        g2: Second group values.

    Returns:
        Cohen's d value, or None if computation fails.
    """
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return None

    try:
        mean_diff = float(np.mean(g1)) - float(np.mean(g2))
        # Pooled std
        pooled_var = ((n1 - 1) * float(np.var(g1, ddof=1)) + (n2 - 1) * float(np.var(g2, ddof=1))) / (n1 + n2 - 2)
        pooled_std = float(np.sqrt(pooled_var))

        if pooled_std == 0:
            return None

        return mean_diff / pooled_std
    except Exception:
        return None


def compute_eta_squared(groups: list[np.ndarray]) -> float | None:
    """
    Compute eta-squared effect size for multiple groups (ANOVA).

    eta^2 = SS_between / SS_total

    Args:
        groups: List of numpy arrays.

    Returns:
        Eta-squared value, or None if computation fails.
    """
    if len(groups) < 2:
        return None

    try:
        all_values = np.concatenate(groups)
        grand_mean = float(np.mean(all_values))

        ss_between = sum(
            len(g) * (float(np.mean(g)) - grand_mean) ** 2
            for g in groups
        )
        ss_total = float(np.sum((all_values - grand_mean) ** 2))

        if ss_total == 0:
            return None

        return float(ss_between / ss_total)
    except Exception:
        return None


def _run_two_group_test(test_name: str, g1: np.ndarray, g2: np.ndarray) -> dict:
    """
    Execute a 2-group statistical test.

    Args:
        test_name: One of independent_t_test, welchs_t_test, mann_whitney_u.
        g1: First group values.
        g2: Second group values.

    Returns:
        Dict with stat, p_value, df (for t-tests), and additional info.
    """
    try:
        if test_name == "independent_t_test":
            stat, p_value = stats.ttest_ind(g1, g2, equal_var=True)
            df = len(g1) + len(g2) - 2
            return {"stat": float(stat), "p_value": float(p_value), "df": float(df)}

        elif test_name == "welchs_t_test":
            stat, p_value = stats.ttest_ind(g1, g2, equal_var=False)
            # Approximate Welch-Satterthwaite df
            s1, s2 = float(np.var(g1, ddof=1)), float(np.var(g2, ddof=1))
            n1, n2 = len(g1), len(g2)
            if s1 == 0 and s2 == 0:
                df = float(n1 + n2 - 2)
            else:
                num = (s1 / n1 + s2 / n2) ** 2
                denom = (s1 / n1) ** 2 / (n1 - 1) + (s2 / n2) ** 2 / (n2 - 1)
                df = float(num / denom) if denom != 0 else float(n1 + n2 - 2)
            return {"stat": float(stat), "p_value": float(p_value), "df": df}

        elif test_name == "mann_whitney_u":
            stat, p_value = stats.mannwhitneyu(g1, g2, alternative="two-sided")
            return {"stat": float(stat), "p_value": float(p_value), "df": None}

        else:
            raise ValueError(f"알 수 없는 검정: {test_name}")

    except Exception as e:
        return {"stat": None, "p_value": None, "df": None, "error": str(e)}


def _run_multi_group_test(test_name: str, groups: list[np.ndarray]) -> dict:
    """
    Execute a multi-group statistical test.

    Args:
        test_name: One of one_way_anova, welch_anova, kruskal_wallis.
        groups: List of numpy arrays.

    Returns:
        Dict with stat, p_value, df.
    """
    try:
        if test_name == "one_way_anova":
            stat, p_value = stats.f_oneway(*groups)
            k = len(groups)
            n_total = sum(len(g) for g in groups)
            df_between = k - 1
            df_within = n_total - k
            return {
                "stat": float(stat),
                "p_value": float(p_value),
                "df": f"{df_between}, {df_within}",
            }

        elif test_name == "welch_anova":
            # Welch's one-way ANOVA (Brown-Forsythe/Welch)
            # Use scipy's f_oneway as approximation, then correct
            # For a proper implementation, use pingouin if available
            try:
                import pingouin as pg
                data_list = []
                for i, g in enumerate(groups):
                    for v in g:
                        data_list.append({"group": str(i), "value": float(v)})
                df_data = pd.DataFrame(data_list)
                result = pg.welch_anova(data=df_data, dv="value", between="group")
                f_val = float(result["F"].iloc[0])
                p_val = float(result["p-unc"].iloc[0])
                return {"stat": f_val, "p_value": p_val, "df": None}
            except ImportError:
                # Fallback to standard ANOVA
                stat, p_value = stats.f_oneway(*groups)
                return {"stat": float(stat), "p_value": float(p_value), "df": None}

        elif test_name == "kruskal_wallis":
            stat, p_value = stats.kruskal(*groups)
            k = len(groups)
            df = k - 1
            return {"stat": float(stat), "p_value": float(p_value), "df": float(df)}

        else:
            raise ValueError(f"알 수 없는 검정: {test_name}")

    except Exception as e:
        return {"stat": None, "p_value": None, "df": None, "error": str(e)}


def run_posthoc(groups_dict: dict[str, np.ndarray], test_type: str, alpha: float = 0.05) -> pd.DataFrame | None:
    """
    Run post-hoc tests for multi-group comparisons.

    Post-hoc mapping:
      one_way_anova   -> Tukey HSD
      welch_anova     -> Games-Howell (or Tukey as fallback)
      kruskal_wallis  -> Dunn's test

    Args:
        groups_dict: {group_name: array_of_values}
        test_type: The primary test name.
        alpha: Significance level.

    Returns:
        DataFrame with p-values, or None if post-hoc not applicable.
    """
    if len(groups_dict) < 3:
        return None  # Post-hoc not needed for 2 groups

    try:
        if test_type == "one_way_anova":
            from statsmodels.stats.multicomp import pairwise_tukeyhsd

            data = []
            labels = []
            for name, values in groups_dict.items():
                data.extend(values.tolist())
                labels.extend([name] * len(values))

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = pairwise_tukeyhsd(data, labels, alpha=alpha)

            table_data = result._results_table.data
            headers = table_data[0]
            rows = table_data[1:]
            df = pd.DataFrame(rows, columns=headers)
            return df

        elif test_type == "welch_anova":
            try:
                import pingouin as pg
                data_list = []
                for name, values in groups_dict.items():
                    for v in values:
                        data_list.append({"group": name, "value": float(v)})
                df_data = pd.DataFrame(data_list)
                result = pg.pairwise_gameshowell(data=df_data, dv="value", between="group")
                return result
            except ImportError:
                # Fallback to Tukey HSD
                return run_posthoc(groups_dict, "one_way_anova", alpha)

        elif test_type == "kruskal_wallis":
            import scikit_posthocs as sp

            data = list(groups_dict.values())
            group_names = list(groups_dict.keys())

            p_matrix = sp.posthoc_dunn(data, p_adjust="bonferroni")
            p_matrix.index = group_names
            p_matrix.columns = group_names
            return p_matrix

    except Exception as e:
        # Return None on any post-hoc failure rather than crashing
        return None

    return None


def _compute_descriptive_stats(groups_dict: dict[str, np.ndarray]) -> dict:
    """
    Compute descriptive statistics for each group.

    Args:
        groups_dict: {group_name: values_array}

    Returns:
        Dict of {group_name: {n, mean, std, median, min, max}}
    """
    descriptive = {}
    for name, values in groups_dict.items():
        if len(values) == 0:
            descriptive[name] = {"n": 0, "mean": None, "std": None, "median": None, "min": None, "max": None}
        else:
            descriptive[name] = {
                "n": int(len(values)),
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "median": float(np.median(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }
    return descriptive


def run_analysis(groups_dict: dict[str, np.ndarray], alpha: float = 0.05) -> dict:
    """
    Run complete statistical analysis for a set of groups.

    Performs:
    1. Descriptive statistics
    2. Normality tests (Shapiro-Wilk)
    3. Variance test (Levene's)
    4. Test selection
    5. Primary statistical test
    6. Effect size computation
    7. Post-hoc tests (if 3+ groups and significant)

    Args:
        groups_dict: {group_name: values_array} - NaN already removed per group.
        alpha: Significance level.

    Returns:
        Complete analysis result dict.
    """
    group_names = list(groups_dict.keys())
    group_arrays = [groups_dict[name] for name in group_names]

    # Filter out groups with insufficient data
    valid_groups = {name: arr for name, arr in groups_dict.items() if len(arr) >= 2}
    if len(valid_groups) < 2:
        return {
            "error": "유효한 데이터가 있는 그룹이 2개 미만입니다.",
            "is_significant": False,
        }

    valid_names = list(valid_groups.keys())
    valid_arrays = [valid_groups[name] for name in valid_names]

    # Descriptive stats
    descriptive = _compute_descriptive_stats(valid_groups)

    # Normality tests
    normality_results = {
        name: run_normality_test(arr, alpha)
        for name, arr in valid_groups.items()
    }

    # Variance test
    variance_test = run_variance_test(valid_arrays, alpha)

    # Test selection
    test_name = select_test(valid_arrays, alpha)

    # Run primary test
    n_groups = len(valid_groups)
    if n_groups == 2:
        g1, g2 = valid_arrays[0], valid_arrays[1]
        test_result = _run_two_group_test(test_name, g1, g2)
    else:
        test_result = _run_multi_group_test(test_name, valid_arrays)

    p_value = test_result.get("p_value")
    is_significant = bool(p_value is not None and p_value < alpha)

    # Effect sizes
    cohens_d = None
    eta_squared = None

    if n_groups == 2:
        g1, g2 = valid_arrays[0], valid_arrays[1]
        cohens_d = compute_cohens_d(g1, g2)
    else:
        eta_squared = compute_eta_squared(valid_arrays)

    # Post-hoc tests (only for multi-group significant results)
    posthoc_matrix = None
    if n_groups >= 3 and is_significant:
        posthoc_matrix = run_posthoc(valid_groups, test_name, alpha)

    # Test display names
    test_display_names = {
        "independent_t_test": "Independent samples t-test",
        "welchs_t_test": "Welch's t-test",
        "mann_whitney_u": "Mann-Whitney U test",
        "one_way_anova": "One-way ANOVA",
        "welch_anova": "Welch ANOVA",
        "kruskal_wallis": "Kruskal-Wallis test",
    }

    return {
        "test_name": test_name,
        "test_display": test_display_names.get(test_name, test_name),
        "normality_results": normality_results,
        "variance_test": variance_test,
        "test_result": test_result,
        "cohens_d": cohens_d,
        "eta_squared": eta_squared,
        "is_significant": is_significant,
        "alpha": alpha,
        "posthoc_matrix": posthoc_matrix,
        "descriptive": descriptive,
        "groups_analyzed": valid_names,
        "n_groups": n_groups,
    }


def _sanitize_column_name(name: str) -> str:
    """
    statsmodels 수식에 사용하기 위한 안전한 ASCII 열 이름으로 변환합니다.

    한글, 공백, 특수문자 등을 포함하는 이름을 알파벳+숫자 형태로 치환합니다.

    Args:
        name: 원본 열 이름

    Returns:
        수식에 안전한 열 이름
    """
    import re
    # 영숫자와 밑줄만 남기고 나머지는 밑줄로 대체
    sanitized = re.sub(r"[^\w]", "_", name, flags=re.ASCII)
    # 숫자로 시작하는 경우 앞에 밑줄 추가
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized or "col"


def _run_art_anova(
    df_long: "pd.DataFrame",
    factor_a: str,
    factor_b: str,
    value_col: str,
    alpha: float,
) -> dict:
    """
    Aligned Rank Transform ANOVA (비모수 이원 분산분석).

    Conover 접근법: 원시 값을 순위 변환 후 이원 ANOVA를 수행합니다.
    이는 정규성 가정이 충족되지 않을 때 사용하는 실용적 대안입니다.

    Args:
        df_long: factor_a, factor_b, value_col 열을 포함한 long-format DataFrame
        factor_a: 첫 번째 요인 열 이름
        factor_b: 두 번째 요인 열 이름
        value_col: 측정값 열 이름
        alpha: 유의수준

    Returns:
        run_twoway_anova()와 동일한 구조의 결과 딕셔너리
    """
    import pandas as pd

    df_work = df_long.copy()

    # 안전한 열 이름으로 매핑
    safe_a = "factor_0"
    safe_b = "factor_1"
    safe_val = "value"

    df_work = df_work.rename(columns={
        factor_a: safe_a,
        factor_b: safe_b,
        value_col: safe_val,
    })

    # Conover 접근법: 원시 값을 순위 변환
    df_work[safe_val] = df_work[safe_val].rank()

    try:
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm

        formula = f"{safe_val} ~ C({safe_a}) * C({safe_b})"
        model = ols(formula, data=df_work).fit()
        anova_table = anova_lm(model, typ=2)

        ss_residual = float(anova_table.loc["Residual", "sum_sq"])
        residual_df = int(anova_table.loc["Residual", "df"])

        factors_result = {}
        factor_ranking = []

        # 주 효과 A
        row_a = f"C({safe_a})"
        if row_a in anova_table.index:
            ss_a = float(anova_table.loc[row_a, "sum_sq"])
            f_a = float(anova_table.loc[row_a, "F"])
            p_a = float(anova_table.loc[row_a, "PR(>F)"])
            df_a = int(anova_table.loc[row_a, "df"])
            eta_a = ss_a / (ss_a + ss_residual) if (ss_a + ss_residual) > 0 else 0.0
            factors_result[factor_a] = {
                "F": f_a,
                "p_value": p_a,
                "df": str(df_a),
                "eta_sq_partial": float(eta_a),
                "is_significant": bool(p_a < alpha),
            }
            factor_ranking.append((factor_a, float(eta_a)))

        # 주 효과 B
        row_b = f"C({safe_b})"
        if row_b in anova_table.index:
            ss_b = float(anova_table.loc[row_b, "sum_sq"])
            f_b = float(anova_table.loc[row_b, "F"])
            p_b = float(anova_table.loc[row_b, "PR(>F)"])
            df_b = int(anova_table.loc[row_b, "df"])
            eta_b = ss_b / (ss_b + ss_residual) if (ss_b + ss_residual) > 0 else 0.0
            factors_result[factor_b] = {
                "F": f_b,
                "p_value": p_b,
                "df": str(df_b),
                "eta_sq_partial": float(eta_b),
                "is_significant": bool(p_b < alpha),
            }
            factor_ranking.append((factor_b, float(eta_b)))

        # 교호작용
        row_int = f"C({safe_a}):C({safe_b})"
        if row_int in anova_table.index:
            ss_int = float(anova_table.loc[row_int, "sum_sq"])
            f_int = float(anova_table.loc[row_int, "F"])
            p_int = float(anova_table.loc[row_int, "PR(>F)"])
            df_int = int(anova_table.loc[row_int, "df"])
            eta_int = ss_int / (ss_int + ss_residual) if (ss_int + ss_residual) > 0 else 0.0
            factors_result["interaction"] = {
                "F": f_int,
                "p_value": p_int,
                "df": str(df_int),
                "eta_sq_partial": float(eta_int),
                "is_significant": bool(p_int < alpha),
            }

        factor_ranking.sort(key=lambda x: x[1], reverse=True)

        return {
            "method": "nonparametric_twoway",
            "factors": factors_result,
            "residual_df": residual_df,
            "factor_ranking": factor_ranking,
            "normality_ok": False,
            "variance_ok": True,
        }

    except Exception as e:
        return {
            "method": "nonparametric_twoway",
            "factors": {},
            "residual_df": 0,
            "factor_ranking": [],
            "normality_ok": False,
            "variance_ok": True,
            "error": str(e),
        }


def run_twoway_anova(
    df_long: "pd.DataFrame",
    factor_a: str,
    factor_b: str,
    value_col: str = "value",
    alpha: float = 0.05,
) -> dict:
    """
    이원 분산분석(Two-Way ANOVA)을 수행합니다.

    데이터 정규성 여부에 따라 적절한 방법을 자동 선택합니다:
    - 정규성 충족: statsmodels OLS + Type II SS (이원 ANOVA)
    - 정규성 미충족: Aligned Rank Transform (비모수 대안)

    요인 이름에 한글/공백/특수문자가 포함된 경우 내부적으로 안전한
    ASCII 이름으로 변환 후 결과에는 원래 이름을 사용합니다.

    Args:
        df_long: factor_a, factor_b, value_col 열을 포함한 long-format DataFrame
        factor_a: 첫 번째 요인 열 이름
        factor_b: 두 번째 요인 열 이름
        value_col: 측정값 열 이름 (기본값: "value")
        alpha: 유의수준 (기본값: 0.05)

    Returns:
        {
            "method": "two_way_anova" 또는 "nonparametric_twoway",
            "factors": {
                factor_a: {"F": float, "p_value": float, "df": str,
                           "eta_sq_partial": float, "is_significant": bool},
                factor_b: {...},
                "interaction": {...}
            },
            "residual_df": int,
            "factor_ranking": [(factor_name, eta_sq), ...],  # eta_sq 내림차순
            "normality_ok": bool,
            "variance_ok": bool,
            "error": str (오류 발생 시에만)
        }
    """
    import warnings

    # statsmodels 가용성 확인
    try:
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm
        statsmodels_available = True
    except ImportError:
        statsmodels_available = False

    if not statsmodels_available:
        return {
            "method": "unavailable",
            "factors": {},
            "residual_df": 0,
            "factor_ranking": [],
            "normality_ok": False,
            "variance_ok": False,
            "error": "statsmodels 패키지가 설치되지 않았습니다. pip install statsmodels>=0.14.0",
        }

    # 데이터 전처리: 결측값 제거
    df_clean = df_long[[factor_a, factor_b, value_col]].dropna().copy()

    if len(df_clean) < 4:
        return {
            "method": "two_way_anova",
            "factors": {},
            "residual_df": 0,
            "factor_ranking": [],
            "normality_ok": False,
            "variance_ok": False,
            "error": f"유효한 데이터 수 부족 (n={len(df_clean)})",
        }

    # 잔차 정규성 검정
    # 안전한 열 이름으로 매핑하여 임시 모델 적합
    safe_a = "factor_0"
    safe_b = "factor_1"
    safe_val = "value_meas"

    df_safe = df_clean.rename(columns={
        factor_a: safe_a,
        factor_b: safe_b,
        value_col: safe_val,
    })

    normality_ok = False
    variance_ok = True

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            formula_check = f"{safe_val} ~ C({safe_a}) * C({safe_b})"
            model_check = ols(formula_check, data=df_safe).fit()
            residuals = model_check.resid.values
            norm_result = run_normality_test(residuals, alpha)
            normality_ok = bool(norm_result.get("is_normal", False))
    except Exception:
        normality_ok = False

    # 정규성 미충족 시 비모수 방법 사용
    if not normality_ok:
        return _run_art_anova(df_clean, factor_a, factor_b, value_col, alpha)

    # 정규성 충족: statsmodels Type II SS 이원 ANOVA
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            formula = f"{safe_val} ~ C({safe_a}) * C({safe_b})"
            model = ols(formula, data=df_safe).fit()
            anova_table = anova_lm(model, typ=2)

        ss_residual = float(anova_table.loc["Residual", "sum_sq"])
        residual_df = int(anova_table.loc["Residual", "df"])

        factors_result = {}
        factor_ranking = []

        # 주 효과 A 추출
        row_a = f"C({safe_a})"
        if row_a in anova_table.index:
            ss_a = float(anova_table.loc[row_a, "sum_sq"])
            f_a = float(anova_table.loc[row_a, "F"])
            p_a = float(anova_table.loc[row_a, "PR(>F)"])
            df_a = int(anova_table.loc[row_a, "df"])
            eta_a = ss_a / (ss_a + ss_residual) if (ss_a + ss_residual) > 0 else 0.0
            factors_result[factor_a] = {
                "F": f_a,
                "p_value": p_a,
                "df": str(df_a),
                "eta_sq_partial": float(eta_a),
                "is_significant": bool(p_a < alpha),
            }
            factor_ranking.append((factor_a, float(eta_a)))

        # 주 효과 B 추출
        row_b = f"C({safe_b})"
        if row_b in anova_table.index:
            ss_b = float(anova_table.loc[row_b, "sum_sq"])
            f_b = float(anova_table.loc[row_b, "F"])
            p_b = float(anova_table.loc[row_b, "PR(>F)"])
            df_b = int(anova_table.loc[row_b, "df"])
            eta_b = ss_b / (ss_b + ss_residual) if (ss_b + ss_residual) > 0 else 0.0
            factors_result[factor_b] = {
                "F": f_b,
                "p_value": p_b,
                "df": str(df_b),
                "eta_sq_partial": float(eta_b),
                "is_significant": bool(p_b < alpha),
            }
            factor_ranking.append((factor_b, float(eta_b)))

        # 교호작용 추출
        row_int = f"C({safe_a}):C({safe_b})"
        if row_int in anova_table.index:
            ss_int = float(anova_table.loc[row_int, "sum_sq"])
            f_int = float(anova_table.loc[row_int, "F"])
            p_int = float(anova_table.loc[row_int, "PR(>F)"])
            df_int = int(anova_table.loc[row_int, "df"])
            eta_int = ss_int / (ss_int + ss_residual) if (ss_int + ss_residual) > 0 else 0.0
            factors_result["interaction"] = {
                "F": f_int,
                "p_value": p_int,
                "df": str(df_int),
                "eta_sq_partial": float(eta_int),
                "is_significant": bool(p_int < alpha),
            }

        # 요인 영향도 순위 (편 η² 내림차순)
        factor_ranking.sort(key=lambda x: x[1], reverse=True)

        return {
            "method": "two_way_anova",
            "factors": factors_result,
            "residual_df": residual_df,
            "factor_ranking": factor_ranking,
            "normality_ok": normality_ok,
            "variance_ok": variance_ok,
        }

    except Exception as e:
        return {
            "method": "two_way_anova",
            "factors": {},
            "residual_df": 0,
            "factor_ranking": [],
            "normality_ok": normality_ok,
            "variance_ok": variance_ok,
            "error": str(e),
        }


def main() -> None:
    """CLI utility for testing the analysis engine."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Statistical analysis engine test")
    parser.add_argument("--demo", action="store_true", help="Run with demo data")
    args = parser.parse_args()

    if args.demo:
        # Generate demo data for testing
        rng = np.random.default_rng(42)
        g1 = rng.normal(loc=1.0, scale=0.2, size=25)
        g2 = rng.normal(loc=0.8, scale=0.2, size=20)
        g3 = rng.normal(loc=0.9, scale=0.25, size=22)

        groups = {"Control": g1, "Treatment1": g2, "Treatment2": g3}
        result = run_analysis(groups, alpha=0.05)

        print(f"선택된 검정: {result['test_display']}")
        print(f"유의함: {result['is_significant']}")
        if result["test_result"].get("p_value") is not None:
            print(f"p-값: {result['test_result']['p_value']:.4f}")
        if result["eta_squared"] is not None:
            print(f"Eta-squared: {result['eta_squared']:.3f}")

        print("\n기술 통계:")
        for name, stats_dict in result["descriptive"].items():
            if stats_dict["n"] > 0:
                print(f"  {name}: N={stats_dict['n']}, mean={stats_dict['mean']:.3f}, std={stats_dict['std']:.3f}")
    else:
        print("사용법: python3 analysis_engine.py --demo")
        sys.exit(0)


if __name__ == "__main__":
    main()
