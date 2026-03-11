# Natural Language Interpretation Templates

Templates for generating human-readable interpretations of statistical results.

---

## Effect Size Magnitude Labels

### Cohen's d (for 2-group comparisons)

| |d| range | Label (EN) | Label (KO) |
|-------------|-----------|------------|
| < 0.2 | negligible | 무시 가능한 (negligible) |
| 0.2 – 0.49 | small | 작은 (small) |
| 0.5 – 0.79 | medium | 중간 (medium) |
| >= 0.8 | large | 큰 (large) |

### Eta-squared η² (for ANOVA)

| η² range | Label (EN) | Label (KO) |
|----------|-----------|------------|
| < 0.01 | negligible | 무시 가능한 |
| 0.01 – 0.059 | small | 작은 |
| 0.06 – 0.139 | medium | 중간 |
| >= 0.14 | large | 큰 |

---

## 2-Group Interpretation Templates

### Significant Result (p < alpha)

```python
SIGNIFICANT_2GROUP_TEMPLATE = """
**{label}** 비교 결과:

{group_a} (평균={mean_a:.3f}, SD={std_a:.3f}, N={n_a}) 와
{group_b} (평균={mean_b:.3f}, SD={std_b:.3f}, N={n_b}) 사이에
통계적으로 유의한 차이가 있었습니다 ({test_display}: {stat_label}={stat_value:.3f}, p={p_value:.4f}).

{factor_sentence}{direction_sentence}{effect_sentence}
"""
```

**Variable definitions:**
- `label`: e.g., "Ref vs Cond.1"
- `test_display`: e.g., "Welch's t-test"
- `stat_label`: "t" for t-test, "U" for Mann-Whitney
- `factor_sentence`: e.g., "EtchingDepth를 6μm에서 16μm으로 변경했을 때, "
- `direction_sentence`: e.g., "{factor}가 증가할수록 측정값이 감소하는 경향을 보였습니다. "
- `effect_sentence`: e.g., "효과 크기는 Cohen's d = 0.72로 중간(medium) 수준입니다."

**Direction logic:**
```python
def get_direction_sentence(mean_a, mean_b, group_a, group_b, measurement_name):
    if mean_b > mean_a:
        return f"{group_b}에서 {measurement_name}이 더 높았습니다 (Δ = +{mean_b - mean_a:.3f}). "
    elif mean_b < mean_a:
        return f"{group_b}에서 {measurement_name}이 더 낮았습니다 (Δ = {mean_b - mean_a:.3f}). "
    else:
        return f"두 그룹의 평균이 동일했습니다. "
```

### Non-Significant Result (p >= alpha)

```python
NON_SIGNIFICANT_2GROUP_TEMPLATE = """
**{label}** 비교 결과:

{group_a} (평균={mean_a:.3f}, SD={std_a:.3f}, N={n_a}) 와
{group_b} (평균={mean_b:.3f}, SD={std_b:.3f}, N={n_b}) 사이에
통계적으로 유의한 차이가 발견되지 않았습니다 ({test_display}: {stat_label}={stat_value:.3f}, p={p_value:.4f}, α={alpha}).

{power_note}
"""
```

**Power note logic:**
```python
def get_power_note(n_a, n_b, alpha):
    min_n = min(n_a, n_b)
    if min_n < 5:
        return ("주의: 샘플 수가 매우 적어 (최소 N={}) 차이가 있더라도 "
                "검출하기 어려울 수 있습니다 (검정력 낮음).").format(min_n)
    elif min_n < 10:
        return ("참고: 샘플 수가 적어 (최소 N={}) 중간 크기의 효과만 "
                "검출 가능할 수 있습니다.").format(min_n)
    else:
        return ""
```

---

## Multi-Group (ANOVA/Kruskal-Wallis) Interpretation Templates

### Significant Overall Result

```python
SIGNIFICANT_MULTIGROUP_TEMPLATE = """
**{label}** 다중 그룹 비교 결과:

{test_display} 결과, {n_groups}개 그룹 간에 통계적으로 유의한 차이가 있었습니다
({stat_label}={stat_value:.3f}, p={p_value:.4f}).

**그룹별 기술 통계:**
{descriptive_table}

{posthoc_summary}

{effect_sentence}
"""
```

**Post-hoc summary template:**
```python
POSTHOC_SUMMARY_TEMPLATE = """
**{posthoc_test_name} 사후 검정 결과** (α={alpha}):
유의한 쌍별 차이:
{significant_pairs_list}

유의하지 않은 쌍:
{nonsignificant_pairs_list}
"""
```

### Non-Significant Overall Result

```python
NON_SIGNIFICANT_MULTIGROUP_TEMPLATE = """
**{label}** 다중 그룹 비교 결과:

{test_display} 결과, {n_groups}개 그룹 간에 통계적으로 유의한 차이가 없었습니다
({stat_label}={stat_value:.3f}, p={p_value:.4f}, α={alpha}).

{power_note}
"""
```

---

## Factor Isolation Interpretation

When the analysis set has `type = "factor_isolation"`:

```python
FACTOR_ISOLATION_TEMPLATE = """
**{isolates_factor} 요인 효과 분석:**

{held_constant_description}을(를) 고정한 조건에서
{isolates_factor}를 {value_a}에서 {value_b}로 변경했을 때의 효과:

{base_interpretation}
"""
```

**Example rendering:**
> **EtchingDepth 요인 효과 분석:**
>
> OpticalSystem=LensA를 고정한 조건에서 EtchingDepth를 6um에서 16um으로 변경했을 때의 효과:
>
> Cond.1 (평균=0.81, SD=0.15, N=17) 와 Cond.3 (평균=0.68, SD=0.12, N=15) 사이에 통계적으로 유의한 차이가 있었습니다 (Welch's t-test: t=2.84, p=0.006).
> Cond.3에서 측정값이 더 낮았습니다 (Δ = -0.13). 효과 크기는 Cohen's d = 0.72로 중간(medium)수준입니다.

---

## Effect Size Sentence Templates

```python
def build_effect_sentence(cohens_d=None, eta_squared=None, effect_size_option="both"):
    """
    Build natural language effect size description.
    effect_size_option: "cohens_d", "eta_squared", "both", "none"
    """
    sentences = []

    if cohens_d is not None and effect_size_option in ("cohens_d", "both"):
        magnitude = get_cohens_d_magnitude(abs(cohens_d))
        sentences.append(
            f"효과 크기는 Cohen's d = {cohens_d:.3f}로 {magnitude} 수준입니다."
        )

    if eta_squared is not None and effect_size_option in ("eta_squared", "both"):
        magnitude = get_eta_squared_magnitude(eta_squared)
        sentences.append(
            f"설명 분산 η² = {eta_squared:.3f} ({magnitude} 효과)."
        )

    return " ".join(sentences) if sentences else ""


def get_cohens_d_magnitude(d_abs):
    if d_abs < 0.2:
        return "무시 가능한 (negligible)"
    elif d_abs < 0.5:
        return "작은 (small)"
    elif d_abs < 0.8:
        return "중간 (medium)"
    else:
        return "큰 (large)"


def get_eta_squared_magnitude(eta_sq):
    if eta_sq < 0.01:
        return "무시 가능한"
    elif eta_sq < 0.06:
        return "작은"
    elif eta_sq < 0.14:
        return "중간"
    else:
        return "큰"
```

---

## Test Name Display Mapping

```python
TEST_DISPLAY_NAMES = {
    "independent_t_test": "독립 표본 t-검정 (Independent samples t-test)",
    "welchs_t_test": "Welch's t-검정 (Welch's t-test)",
    "mann_whitney_u": "Mann-Whitney U 검정 (비모수)",
    "one_way_anova": "일원 분산분석 (One-way ANOVA)",
    "welch_anova": "Welch의 일원 분산분석 (Welch ANOVA)",
    "kruskal_wallis": "Kruskal-Wallis 검정 (비모수)",
}

TEST_STAT_LABELS = {
    "independent_t_test": "t",
    "welchs_t_test": "t",
    "mann_whitney_u": "U",
    "one_way_anova": "F",
    "welch_anova": "F",
    "kruskal_wallis": "H",
}
```

---

## Report Section Header Templates

```markdown
## 분석 {index}: {analysis_set_label}

**비교:** {group_a} vs {group_b}
**검정:** {test_display}
**결과:** {'유의함 ✓' if significant else '유의하지 않음'}
**p-값:** {p_value:.4f} (α = {alpha})
```

---

## Summary Table Template (at top of report)

```markdown
## 분석 요약

| # | 비교 | 검정 | 통계량 | p-값 | 유의함? | Cohen's d |
|---|------|------|--------|------|---------|-----------|
| 1 | Ref vs Cond.1 | Welch's t | t=2.84 | 0.006 | ✓ | 0.72 (중간) |
| 2 | Ref vs Cond.2 | Mann-Whitney | U=156 | 0.241 | - | - |
| 3 | Cond.1 vs Cond.3 | Welch's t | t=1.21 | 0.234 | - | 0.31 (작은) |
```

---

## Factorial Analysis Interpretation Templates

### Factor Impact Comparison Table Template

```markdown
## 요인별 영향도 분석

**분석 방법:** {method_display}

| 요인 | F값 | p-값 | 편 η² | 영향도 |
|------|-----|------|-------|--------|
| {factor_a} | {F_a:.1f} | {p_a_str} | {eta_a:.3f} | {stars_a} {magnitude_a} |
| {factor_b} | {F_b:.1f} | {p_b_str} | {eta_b:.3f} | {stars_b} {magnitude_b} |
| 교호작용 ({factor_a}×{factor_b}) | {F_int:.1f} | {p_int_str} | {eta_int:.3f} | {stars_int} {magnitude_int} |
```

### Factor Ranking Templates

**Both factors significant, no interaction:**
```python
BOTH_SIGNIFICANT_TEMPLATE = """
**결론:** {factor_a}({eta_a_label}, 편 η²={eta_a:.3f})가 {factor_b}({eta_b_label}, 편 η²={eta_b:.3f})보다
{measurement}에 약 {ratio:.1f}배 더 큰 영향을 미칩니다. 두 요인 모두 통계적으로 유의합니다 (α = {alpha}).
"""
```

**Both significant, interaction present:**
```python
BOTH_SIGNIFICANT_INTERACTION_TEMPLATE = """
**결론:** {factor_a}(편 η²={eta_a:.3f})와 {factor_b}(편 η²={eta_b:.3f}) 모두 {measurement}에 유의한 영향을 미칩니다.
교호작용이 유의하여 (p = {p_int_str}), 두 요인의 효과가 독립적이지 않습니다 —
{factor_a}의 효과가 {factor_b}의 수준에 따라 달라집니다.
"""
```

**Only one factor significant:**
```python
ONE_SIGNIFICANT_TEMPLATE = """
**결론:** {sig_factor}(편 η²={eta_sig:.3f})만 {measurement}에 통계적으로 유의한 영향을 미쳤으며,
{nonsig_factor}(p = {p_nonsig_str})는 유의한 영향을 미치지 않았습니다.
"""
```

**Neither factor significant:**
```python
NEITHER_SIGNIFICANT_TEMPLATE = """
**결론:** 분석된 요인 중 {measurement}에 통계적으로 유의한 영향을 미치는 요인이 없었습니다 (α = {alpha}).
"""
```

### Star Rating Logic

```python
def get_impact_stars(eta_sq: float, is_significant: bool) -> str:
    if not is_significant:
        return "유의하지 않음"
    if eta_sq >= 0.14:
        return "★★★ 큰 효과"
    elif eta_sq >= 0.06:
        return "★★ 중간 효과"
    elif eta_sq >= 0.01:
        return "★ 작은 효과"
    else:
        return "무시 가능"
```

### Layman Explanation for Two-Way ANOVA

```python
TWOWAY_ANOVA_LAYMAN = """
두 가지 실험 조건(예: 광학계 종류와 에칭량)이 결과에 미치는 영향을 동시에 분석하는 방법입니다.
각 조건이 독립적으로 얼마나 영향을 주는지, 그리고 두 조건이 함께 작용할 때
추가적인 효과(교호작용)가 있는지 확인합니다.
"""

RANK_TWOWAY_LAYMAN = """
데이터가 정규분포를 따르지 않아, 원래 값 대신 순위(rank)를 사용하여 분석했습니다.
해석 방식은 일반 Two-Way ANOVA와 동일합니다.
"""
```
