# Statistical Test Selection Logic

Complete decision tree for selecting the appropriate statistical test based on data characteristics.

---

## Prerequisites Check

Before running any statistical test:

1. **Remove NaN values** for the specific groups being compared
2. **Check minimum sample size**: n >= 2 required; n >= 3 recommended for normality testing
3. **Verify data is numeric**: non-numeric columns should be excluded with a warning

---

## Normality Testing: Shapiro-Wilk

### When to Run

Run Shapiro-Wilk for each group separately before selecting the primary test.

### Thresholds

| Condition | Result |
|-----------|--------|
| p_value > alpha | Group is considered normally distributed |
| p_value <= alpha | Group is NOT normally distributed |
| n < 3 | Cannot test — assume non-normal (conservative) |
| n >= 50 | Shapiro-Wilk may be overly sensitive; also check skewness |

### Implementation

```python
from scipy import stats

def run_normality_test(data: np.ndarray, alpha: float = 0.05) -> dict:
    """
    Run Shapiro-Wilk normality test.

    Returns:
        dict with keys: stat, p_value, is_normal, n, note
    """
    data_clean = data[~np.isnan(data)]
    n = len(data_clean)

    if n < 3:
        return {
            "stat": None,
            "p_value": None,
            "is_normal": False,
            "n": n,
            "note": "Too few samples (n < 3). Assumed non-normal."
        }

    if n > 5000:
        # Shapiro-Wilk is not suitable for very large samples
        # Use D'Agostino-Pearson test instead
        stat, p_value = stats.normaltest(data_clean)
    else:
        stat, p_value = stats.shapiro(data_clean)

    return {
        "stat": float(stat),
        "p_value": float(p_value),
        "is_normal": bool(p_value > alpha),
        "n": n,
        "note": None
    }
```

### Sample Size Caveats

- **n < 3**: Cannot perform normality test. Treat as non-normal.
- **n = 3–7**: Shapiro-Wilk has low power; normality assumption is hard to verify. Prefer non-parametric if in doubt.
- **n = 8–50**: Shapiro-Wilk is most reliable in this range.
- **n > 50**: Shapiro-Wilk detects even trivial departures. Consider robust parametric tests.

---

## Variance Equality Testing: Levene's Test

### Purpose

Levene's test checks whether multiple groups have equal variances (homoscedasticity).

### When to Run

Run Levene's test after normality check, before selecting between t-test variants or ANOVA variants.

### Thresholds

| Condition | Result |
|-----------|--------|
| p_value > alpha | Variances are considered equal |
| p_value <= alpha | Variances are NOT equal |
| n < 2 per group | Cannot test — skip Levene's |

```python
from scipy import stats

def run_variance_test(groups: list[np.ndarray], alpha: float = 0.05) -> dict:
    """
    Run Levene's test for equality of variances.

    Args:
        groups: List of arrays (NaN already removed)

    Returns:
        dict with keys: stat, p_value, equal_variance
    """
    # Filter groups with at least 2 samples
    valid_groups = [g for g in groups if len(g) >= 2]

    if len(valid_groups) < 2:
        return {
            "stat": None,
            "p_value": None,
            "equal_variance": True,  # Assume equal if cannot test
            "note": "Insufficient samples for Levene's test"
        }

    stat, p_value = stats.levene(*valid_groups, center='median')

    return {
        "stat": float(stat),
        "p_value": float(p_value),
        "equal_variance": bool(p_value > alpha),
        "note": None
    }
```

---

## Complete Decision Tree

```
                     ┌─────────────────────────────┐
                     │  How many groups to compare? │
                     └─────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │ 2 groups                     │ 3+ groups
               ▼                              ▼
   ┌───────────────────────┐     ┌────────────────────────┐
   │ All groups normal?    │     │ All groups normal?      │
   │ (Shapiro-Wilk)        │     │ (Shapiro-Wilk)          │
   └───────────────────────┘     └────────────────────────┘
          │              │                │              │
         YES             NO              YES             NO
          │              │                │              │
          ▼              ▼                ▼              ▼
   ┌──────────┐  ┌───────────────┐  ┌──────────┐  ┌─────────────┐
   │ Equal    │  │ Mann-Whitney  │  │ Equal    │  │Kruskal-     │
   │ variance?│  │ U test        │  │ variance?│  │Wallis test  │
   │(Levene's)│  └───────────────┘  │(Levene's)│  └─────────────┘
   └──────────┘                     └──────────┘
       │      │                         │      │
      YES     NO                       YES     NO
       │      │                         │      │
       ▼      ▼                         ▼      ▼
   ┌──────┐ ┌────────┐            ┌──────────┐ ┌──────────┐
   │ Ind. │ │Welch's │            │ One-way  │ │ Welch    │
   │t-test│ │t-test  │            │  ANOVA   │ │  ANOVA   │
   └──────┘ └────────┘            └──────────┘ └──────────┘
                                       │              │
                                  Post-hoc       Post-hoc
                                  Tukey HSD   Games-Howell
```

---

## Test Descriptions

### 2-Group Tests

#### Independent Samples t-test
- **When**: 2 groups, both normal, equal variances
- **Assumption**: normality + equal variances
- **scipy call**: `stats.ttest_ind(a, b, equal_var=True)`

#### Welch's t-test
- **When**: 2 groups, both normal, unequal variances OR unequal sample sizes
- **Advantage**: More robust; preferred as default for 2-group parametric
- **scipy call**: `stats.ttest_ind(a, b, equal_var=False)`

#### Mann-Whitney U test
- **When**: 2 groups, at least one non-normal
- **Also known as**: Wilcoxon rank-sum test
- **scipy call**: `stats.mannwhitneyu(a, b, alternative='two-sided')`

### 3+ Group Tests

#### One-Way ANOVA
- **When**: 3+ groups, all normal, equal variances
- **scipy call**: `stats.f_oneway(*groups)`

#### Welch ANOVA
- **When**: 3+ groups, all normal, unequal variances
- **scipy call**: `stats.welch_anova` (via pingouin or manual implementation)
- **Alternative**: Use `pingouin.welch_anova(data, dv, between)`

#### Kruskal-Wallis test
- **When**: 3+ groups, at least one non-normal
- **Non-parametric alternative to ANOVA**
- **scipy call**: `stats.kruskal(*groups)`

---

## Post-Hoc Test Selection

Post-hoc tests are run only when the primary test (ANOVA or Kruskal-Wallis) is significant AND there are 3+ groups.

| Primary Test | Post-Hoc Test | Notes |
|-------------|---------------|-------|
| One-way ANOVA (equal var) | Tukey HSD | Controls family-wise error rate |
| Welch ANOVA (unequal var) | Games-Howell | Robust to unequal variance and sample sizes |
| Kruskal-Wallis | Dunn's test | Non-parametric pairwise comparisons |

### Tukey HSD Implementation

```python
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def run_tukey_hsd(groups_dict: dict) -> pd.DataFrame:
    """
    Run Tukey HSD post-hoc test.

    Args:
        groups_dict: {group_name: array_of_values}

    Returns:
        DataFrame with columns: group1, group2, meandiff, p_adj, lower, upper, reject
    """
    data = []
    labels = []
    for name, values in groups_dict.items():
        data.extend(values)
        labels.extend([name] * len(values))

    result = pairwise_tukeyhsd(data, labels)
    df = pd.DataFrame(data=result._results_table.data[1:],
                      columns=result._results_table.data[0])
    return df
```

### Games-Howell Implementation

```python
import pingouin as pg

def run_games_howell(groups_dict: dict) -> pd.DataFrame:
    """
    Run Games-Howell post-hoc test (robust to unequal variances).
    Requires pingouin library.
    """
    data_list = []
    for name, values in groups_dict.items():
        for v in values:
            data_list.append({"group": name, "value": v})

    df = pd.DataFrame(data_list)
    result = pg.pairwise_gameshowell(data=df, dv='value', between='group')
    return result
```

### Dunn's Test Implementation

```python
import scikit_posthocs as sp

def run_dunns_test(groups_dict: dict) -> pd.DataFrame:
    """
    Run Dunn's test post-hoc for Kruskal-Wallis.

    Returns:
        DataFrame with p-values matrix (p-value adjustment: Bonferroni or Holm)
    """
    data = list(groups_dict.values())
    group_names = list(groups_dict.keys())

    p_matrix = sp.posthoc_dunn(data, p_adjust='bonferroni')
    p_matrix.index = group_names
    p_matrix.columns = group_names
    return p_matrix
```

---

## Two-Way ANOVA Decision Tree

### When to Use

Two-Way ANOVA is used when:
- The experimental design has 2+ independent factors
- Each factor has 2+ levels
- The goal is to compare which factor has a greater effect on the outcome

### Decision Tree

```
                ┌─────────────────────────────────────┐
                │  Factorial Design Detected (2+ factors)  │
                └─────────────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │ Residuals normal?            │
               │ (Shapiro-Wilk on residuals)  │
               └──────────────────────────────┘
                    │                    │
                   YES                   NO
                    │                    │
                    ▼                    ▼
       ┌───────────────────┐  ┌──────────────────────┐
       │ Two-Way ANOVA     │  │ Rank-based Two-Way   │
       │ (Type II SS)      │  │ ANOVA (Conover)      │
       │ statsmodels OLS   │  │ Rank transform +     │
       │ + anova_lm        │  │ standard ANOVA       │
       └───────────────────┘  └──────────────────────┘
                    │                    │
                    └──────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │ Report for each effect:  │
              │  - Factor A main effect  │
              │  - Factor B main effect  │
              │  - A×B interaction       │
              │  - Partial η² per effect │
              └──────────────────────────┘
```

### Partial Eta-Squared

Partial eta-squared measures the proportion of variance explained by each factor, controlling for other factors:

```
partial η² = SS_effect / (SS_effect + SS_residual)
```

| partial η² range | Label (EN) | Label (KO) |
|-----------------|-----------|------------|
| < 0.01 | negligible | 무시 가능한 |
| 0.01 – 0.059 | small | 작은 |
| 0.06 – 0.139 | medium | 중간 |
| >= 0.14 | large | 큰 |

### Non-Parametric Alternative

When residuals are not normally distributed:

1. **Aligned Rank Transform (ART)**: Align data by subtracting other effects, rank the aligned values, then run standard ANOVA
2. **Simplified Conover approach**: Rank the raw values, then run Two-Way ANOVA on ranks. This is simpler and works well in practice.

The skill uses the Conover approach (rank-based ANOVA) as the non-parametric fallback.

### Interaction Effect

- **Significant interaction** (p < alpha): The effect of one factor depends on the level of the other factor. The main effects should be interpreted with caution.
- **Non-significant interaction**: The effects of the two factors are independent. Main effects can be directly compared.

---

## Special Cases

### All Groups Have n < 3

When sample sizes are extremely small:
- Cannot run normality test
- Cannot reliably run any parametric test
- **Recommendation**: Use Mann-Whitney U (2 groups) or Kruskal-Wallis (3+ groups) as conservative choice
- **Warning to user**: "샘플 수가 매우 적어 통계적 검정력이 낮습니다. 결과 해석에 주의가 필요합니다."

### Single Group (All Values Same)

If a group has zero variance (all values identical):
- Levene's test will produce NaN
- t-test will produce NaN or raise
- **Handle**: Return special result `{"error": "zero_variance", "group": name}`

### Only 1 Sample in a Group

If a group has n=1 after removing NaN:
- Cannot compute statistics
- **Recommendation**: Exclude this group from analysis
- **Warning to user**: "열 '{col}'의 유효한 값이 1개뿐입니다. 분석에서 제외됩니다."
