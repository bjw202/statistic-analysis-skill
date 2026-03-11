# Questioning Protocol — Edge Cases and Batch Mode

Detailed guide on how to handle special situations during the user interview phases.

---

## Handling Missing Data

When the data summary (Step 2) shows columns with different N values due to NaN rows:

**Display to user:**
```
열 'Cond.1' 에 결측값이 있습니다: 29개 행 중 12개만 유효 (결측 = 12)
```

**Ask:** "결측 데이터 처리 방법을 선택해주세요:"
- 결측값 있는 행 제외 (listwise deletion) — 각 비교에서 유효한 값만 사용 (권장)
- 평균값으로 대체 (mean imputation) — 결측값을 열 평균으로 채움
- 이 열을 분석에서 제외

**Default behavior:** Always use listwise deletion (exclude NaN rows per comparison pair).
This means groups can have different N values, which is expected and valid.

### Why Columns Have Different Lengths

Excel data often has ragged arrays: if an experiment has fewer replications for some conditions,
the shorter columns are padded with NaN. The data loader drops NaN for each column independently.

---

## Handling Mismatched Sample Sizes

When groups in a comparison have very different N:

**Warning trigger:** if max(N) / min(N) > 3

**Display to user:**
```
경고: 비교 그룹 간 샘플 수 차이가 큽니다
  Ref: N=29
  Cond.1: N=8
  비율: 3.6x
```

**Ask:** "불균등한 샘플 수로 계속 진행하시겠습니까?"
- 예, 계속 진행 — Welch's t-test가 불균등 분산/샘플에 더 강건합니다
- 이 비교를 건너뜁니다

**Note:** Welch's t-test is automatically selected when sample sizes differ, regardless of
variance equality. This handles the imbalance appropriately.

---

## Batch Mode (10+ Non-Control Columns)

When there are 10 or more treatment columns, individual Q2.1–Q2.3 per column is impractical.

### Batch Mode Trigger

```python
if len(non_control_columns) >= 10:
    use_batch_mode()
```

### Batch Mode Template

Display this template to the user and ask them to fill it in:

```
아래 표를 복사하여 각 열의 정보를 채워주세요.
빈 칸: 요인명=값 형식으로 입력하세요 (복합 요인은 줄바꿈으로 구분)

열 이름    | 설명                    | 요인 (FactorName=Value)
-----------|------------------------|------------------------
Cond.1     | [설명을 입력하세요]      | EtchingDepth=6um
Cond.2     | [설명을 입력하세요]      | EtchingDepth=10um
Cond.3     | [설명을 입력하세요]      | EtchingDepth=6um
           |                        | OpticalSystem=LensB
...
```

### Parsing Batch Mode Input

Accept the user's filled-in table as free text. Parse it line by line:

```python
def parse_batch_table(text: str, column_names: list) -> dict:
    """
    Parse pipe-delimited table text into column annotations.
    Returns dict: {col_name: {"label": str, "factors": {FactorName: value}}}
    """
    result = {}
    lines = [l.strip() for l in text.strip().split('\n') if '|' in l]

    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 3:
            continue
        col_name = parts[0].strip()
        if col_name not in column_names or col_name == '열 이름' or col_name.startswith('-'):
            continue
        label = parts[1].strip()
        factors_text = parts[2].strip()
        factors = parse_factor_text(factors_text)
        result[col_name] = {"label": label, "factors": factors}

    return result
```

---

## Parsing FactorName=Value Text Responses

When the user types factor information in Q2.3a or Q2.3b:

### Input Format Examples

Single factor:
```
EtchingDepth=6um
```

Multiple factors (one per line):
```
EtchingDepth=6um
OpticalSystem=LensA
LaserPower=High
```

### Parser Implementation

```python
def parse_factor_text(text: str) -> dict:
    """
    Parse 'FactorName=Value' text, one factor per line.
    Handles: spaces around =, empty lines, comment lines starting with #

    Returns: {"FactorName": "Value", ...}
    """
    factors = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            # Try to interpret as single factor with no value
            factors[line] = "true"
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        if key:
            factors[key] = value
    return factors
```

### Validation

After parsing, validate:
- At least one factor must be provided for treatment columns
- Factor names should be alphanumeric (warn on special characters)
- Same factor name should be spelled consistently across columns (case-insensitive comparison)

**If factor names differ by case only** (e.g., "etchingDepth" vs "EtchingDepth"):
```
경고: 요인 이름의 대소문자가 일치하지 않습니다:
  'etchingDepth' (Cond.1) vs 'EtchingDepth' (Cond.3)
표준화할까요? → 예 권장
```

---

## Direct Comparison Specification (Q3.1 = "직접 지정")

When the user selects "직접 지정" for analysis intent:

**Ask:** "비교할 그룹 쌍을 입력해주세요 (한 줄에 하나씩):\n예:\nRef vs Cond.1\nRef vs Cond.2\nCond.1 vs Cond.3"

**Parser:**
```python
def parse_custom_comparisons(text: str, all_columns: list) -> list:
    """
    Parse custom comparison specifications.
    Returns list of (col_a, col_b) tuples.
    """
    pairs = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # Support: "A vs B", "A versus B", "A,B", "A - B"
        for sep in [' vs ', ' versus ', ',', ' - ']:
            if sep in line:
                parts = [p.strip() for p in line.split(sep, 1)]
                if len(parts) == 2:
                    a, b = parts
                    if a in all_columns and b in all_columns:
                        pairs.append((a, b))
                    else:
                        print(f"경고: 열을 찾을 수 없습니다: {a} 또는 {b}")
                    break
    return pairs
```

---

## Alpha Value Custom Input (Q3.2 = "직접 입력")

When the user selects "직접 입력":

**Ask:** "유의수준 alpha 값을 입력해주세요 (예: 0.05, 0.01):"

**Validation:**
- Must be a float between 0.001 and 0.5
- If out of range, show warning and ask again
- Common values: 0.05, 0.01, 0.10, 0.001

---

## Output Path Custom Input (Q3.4 = "직접 경로 입력")

When the user selects "직접 경로 입력":

**Ask:** "보고서를 저장할 폴더 경로를 입력해주세요:"

**Validation:**
- Check if directory exists using `os.path.isdir()`
- If not exists, ask: "폴더가 존재하지 않습니다. 생성할까요?"
- If user says yes, create with `os.makedirs(path, exist_ok=True)`

---

## Replicate Detection Protocol

### Detection Algorithm

After all column annotations are complete:

```python
def detect_replicates(columns: dict) -> dict:
    """
    Group columns by identical factor combinations.

    Returns: {factor_key: [col_names]}
    where factor_key is a frozenset of (factor_name, factor_value) tuples
    """
    groups = {}
    for name, info in columns.items():
        if info.get("role") == "control":
            continue
        factors = info.get("factors", {})
        key = frozenset(factors.items())
        if key not in groups:
            groups[key] = []
        groups[key].append(name)
    return {k: v for k, v in groups.items() if len(v) >= 2}
```

### User Confirmation

Always ask user to confirm replicate detection before pooling:
- Show which columns will be pooled
- Explain that pooling increases statistical power
- Offer option to keep columns separate

### Pooling Behavior

When user confirms pooling:
- Data from replicate columns is concatenated (not averaged)
- Original column identifiers are preserved in the source_column field
- The pooled group uses the shared factor combination as its label

---

## Factorial Design Detection Protocol

### Detection Algorithm

```python
def detect_factorial_design(columns: dict) -> dict | None:
    """
    Check if column factors form a complete or near-complete factorial design.
    """
    all_factors = {}  # {factor_name: set_of_levels}

    for name, info in columns.items():
        factors = info.get("factors", {})
        for fname, fval in factors.items():
            if fname not in all_factors:
                all_factors[fname] = set()
            all_factors[fname].add(fval)

    # Need at least 2 factors with 2+ levels each
    valid_factors = {k: sorted(v) for k, v in all_factors.items() if len(v) >= 2}

    if len(valid_factors) < 2:
        return None

    # Build design label
    dims = [str(len(v)) for v in valid_factors.values()]
    design_label = "×".join(dims)

    return {
        "factors": {k: list(v) for k, v in valid_factors.items()},
        "design_label": design_label
    }
```

### Important: Control Column Factor Annotation

For factorial design detection to work correctly, the control column MUST also have factor annotations.

During Step 4 annotation, if the user sets a control column, the AI should:
1. Infer the control's factor values from the experiment description
2. Ask the user to confirm: "컨트롤 열 'Ref'의 요인 값을 확인해주세요: 광학계=기존, 에칭량=6 — 맞나요?"
3. Store these factors in the control column's config

This ensures the control is properly included in the factorial design matrix.

---

## Analysis Intent Auto-Suggestion

When factorial design is detected (2+ factors with 2+ levels):
- **Auto-suggest "요인별 영향도 비교"** as the recommended option in Q3.1
- Explain that this uses Two-Way ANOVA to determine which factor has greater impact
- Note that pairwise comparisons are also included for detailed per-condition results

When only one varying factor is detected:
- **Auto-suggest "컨트롤과의 유의차 확인"** (existing default)
- The single factor can only be compared via pairwise tests

When no clear factor structure:
- **Auto-suggest "전체 요인 분석"** for exploratory analysis
