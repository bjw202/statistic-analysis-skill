---

name: statistic-analysis description: &gt; Interactive statistical analysis skill for Excel experimental data. Guides users through column annotation, auto-constructs comparison groups, selects appropriate statistical tests (t-test, ANOVA, Kruskal-Wallis), and generates a Markdown dashboard with box plots and natural language interpretations. Use when analyzing experimental conditions from Excel files with control/treatment groups. license: Apache-2.0 compatibility: Designed for Claude Code allowed-tools: Read, Write, Glob, Bash, AskUserQuestion user-invocable: true metadata: version: "1.1.0" category: "workflow" status: "active" updated: "2026-03-11" modularized: "true" tags: "statistics, excel, analysis, experimental-data, visualization, scientific, factorial-design, two-way-anova" argument-hint: "\[path/to/data.xlsx\] \[--sheet SHEET_NAME\]"

# MoAI Extension: Progressive Disclosure

progressive_disclosure: enabled: true level1_tokens: 100 level2_tokens: 5000

# MoAI Extension: Triggers

## triggers: keywords: \["statistics", "Excel", "xlsx", "ANOVA", "t-test", "p-value", "significance", "experimental data", "control group", "box plot", "유의차", "통계 분석"\] phases: \["run"\]

## Quick Reference

Statistical Analysis Skill — Interactive Excel experimental data analysis with automatic test selection and dashboard generation.

Auto-Triggers: .xlsx files, statistical significance discussions, experimental conditions

Core Capabilities:

- Guided column annotation (control vs treatment, factor identification)
- Auto-construction of comparison groups (pairwise, factor-isolated, aggregated)
- Normality + variance testing → auto parametric/non-parametric test selection
- Box plots with significance brackets (embedded PNG)
- Natural language interpretations with effect sizes

Usage: `/statistic-analysis path/to/data.xlsx [--sheet SheetName]`

---

## Execution Directive

When this skill is activated with `/statistic-analysis [args]`:

### Step 1 — Parse Arguments

Extract the Excel file path from `$ARGUMENTS`. If not provided, ask the user for the file path. Optionally extract `--sheet SHEET_NAME` flag (default: first sheet named "Data" or the first sheet).

### Step 2 — Load and Preview Data

Run:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/data_loader.py <excel_path> --summary
```

Display the column summary output to the user before asking any questions.

### Step 3 — Phase 1: Data Overview

Ask these questions in sequence:

**Q1.1** (free text): "이 실험을 1-2 문장으로 설명해주세요. 측정하는 것은 무엇이며, 각 열은 무엇을 나타내나요?"

**Q1.2** (4-choice): "측정값의 타입은 무엇인가요?"

- 연속형 측정값 (권장) — 예: 길이, 강도, 반지름
- 비율/정규화 값 — 예: 퍼센트, 배수
- 이진값 (합격/불합격) — 0 또는 1로 인코딩됨
- 잘 모르겠습니다

**Q1.3** (dynamic choice, options = column names + "없음"): "어느 열이 컨트롤/참조 그룹인가요?"

### Step 4 — Phase 2: Column Annotation

For each non-control column C (process one at a time):

**Q2.1** (free text): "열 '{C}' 는 어떤 실험 조건을 나타내나요? 예: '레이저 출력 6μm 에칭'"

**Q2.2** (2-choice): "이 열은 여러 독립적 실험 요인의 조합인가요?"

- 예 — 예: 에칭 깊이 AND 광학계 같은 복합 요인
- 아니오 — 컨트롤에서 단일 요인만 변경됨

If "예": **Q2.3a** (free text): "각 요인과 값을 한 줄씩 입력하세요:\\nFactorName=Value\\n예:\\nEtchingDepth=6um\\nOpticalSystem=LensA"

If "아니오": **Q2.3b** (free text): "변경된 요인과 값을 입력하세요:\\nFactorName=Value\\n예: EtchingDepth=6um"

> If there are 10+ non-control columns, use batch mode instead: Show a table template and ask user to fill all columns at once.

### Step 4.5 — Replicate Detection

After all columns are annotated, auto-detect columns with identical factor combinations.

**Algorithm**: Group non-control columns by their factor dict. If 2+ columns share identical factors, they are replicates.

**If replicates found, display to user:**

```
반복 실험 감지:
  그룹 A: Cond.1, Cond.2 → 광학계=개선, 에칭량=6
  그룹 B: Cond.3, Cond.4 → 광학계=개선, 에칭량=16
```

**Q_REP** (2-choice): "동일 조건의 열들이 감지되었습니다. 반복 실험 데이터로 처리하여 풀링(pooling)할까요?"

- 예 (권장) — 동일 조건의 데이터를 합쳐서 통계적 검정력을 높입니다
- 아니오 — 각 열을 별도 조건으로 유지합니다

### Step 4.6 — Factorial Design Detection

After replicate detection, auto-detect factorial design from factor structure.

**Algorithm**: Collect all factor names and their unique levels across all columns (including control). If 2+ factors each with 2+ levels exist, it's a factorial design.

**If factorial design detected, display to user:**

```
요인 설계 감지: 2×2
  요인 1: 광학계 → [기존, 개선]
  요인 2: 에칭량 → [6, 16]
```

> This information is used to auto-suggest "요인별 영향도 비교" in Q3.1 and to enable Two-Way ANOVA.

### Step 5 — Phase 3: Analysis Intent

**Q3.1** (4-choice, context-aware): "이 분석의 주요 목적은 무엇인가요?"

If factorial design was detected (Step 4.6):

- 요인별 영향도 비교 (권장) — Two-Way ANOVA로 각 요인의 주효과와 교호작용을 분석하고, 어떤 요인이 더 큰 영향을 미치는지 비교합니다. 동시에 컨트롤 대비 개별 조건 비교도 수행합니다.
- 컨트롤과의 유의차 확인 — 각 조건을 컨트롤과 개별 비교합니다 (기존 방식)
- 전체 요인 분석 — 모든 쌍별 비교를 수행합니다
- 직접 지정 — 비교할 조합을 직접 지정합니다

If factorial design was NOT detected (single factor or no clear structure):

- 컨트롤과의 유의차 확인 (권장) — 각 조건을 컨트롤과 비교
- 특정 요인의 효과 분리 — 하나의 요인만 다른 조건 쌍 비교
- 전체 요인 분석 — 모든 쌍별 비교
- 직접 지정 — 비교할 조합을 직접 지정

**Q3.2** (4-choice): "유의수준(alpha)은 무엇으로 설정할까요?"

- α = 0.05 (권장 — 표준 과학적 기준)
- α = 0.01 (엄격)
- α = 0.10 (탐색적 분석)
- 직접 입력

**Q3.3** (4-choice, context-aware): "효과 크기(effect size) 지표는 무엇으로 보고할까요?"

If Q3.1 = "요인별 영향도 비교":

- 편 Eta-squared (편 η²) (권장) — 요인별 설명 분산 비율. 요인 영향도 비교에 최적
- Cohen's d — 개별 쌍 비교에 적합한 효과 크기
- 둘 다 보고 — 요인별 η²와 개별 비교별 Cohen's d 모두 보고
- 효과 크기 없이 p-값만

Otherwise (existing options):

- Cohen's d (권장 — 연속 측정값에 적합)
- Eta-squared (η²) — ANOVA 설계에 적합
- 둘 다 보고
- 효과 크기 없이 p-값만

**Q3.4** (4-choice): "분석 보고서를 어디에 저장할까요?"

- 입력 엑셀 파일과 같은 폴더 (권장)
- 현재 작업 디렉토리
- 직접 경로 입력
- 저장 없이 터미널에만 출력

### Step 6 — Build Config

Assemble `analysis_config.json` from all answers and write it using the Write tool. Path: same directory as the Excel file, named `analysis_config.json`.

Schema:

```json
{
  "experiment": {
    "description": "user's Q1.1 answer",
    "measurement_type": "continuous|ratio|binary|unknown",
    "control_column": "Ref"
  },
  "columns": {
    "Ref": {
      "role": "control",
      "label": "Control/Reference",
      "factors": {
        "광학계": "기존",
        "에칭량": "6"
      }
    },
    "Cond.1": {
      "role": "treatment",
      "label": "user's Q2.1 answer",
      "factors": {
        "광학계": "개선",
        "에칭량": "6"
      }
    }
  },
  "replicates": {
    "group_1": ["Cond.1", "Cond.2"],
    "group_2": ["Cond.3", "Cond.4"]
  },
  "factorial_design": {
    "factors": {"광학계": ["기존", "개선"], "에칭량": ["6", "16"]},
    "design_label": "2×2"
  },
  "analysis": {
    "primary_goal": "factor_impact_comparison|pairwise_vs_control|factor_isolation|full_factorial|custom",
    "alpha": 0.05,
    "effect_size": "partial_eta_squared|cohens_d|eta_squared|both|none",
    "output_path": "/path/to/output/dir"
  }
}
```

### Step 7 — Run Analysis

```
python3 ${CLAUDE_SKILL_DIR}/scripts/statistic_analyzer.py <excel_path> <config_path>
```

Capture stdout. If exit code != 0, display the error and stop.

### Step 8 — Display Results

Read the generated `analysis_report.md`. Display:

- **For factor_impact_comparison**: Factor impact comparison table (which factor has greater effect), interaction significance, and the number of pairwise comparisons
- **For other intents**: Number of analysis sets run, which comparisons were significant (p &lt; alpha)
- Path to the full report

### Step 9 — Next Steps

Ask: "다음 작업을 선택하세요:"

- 다른 alpha 값으로 재분석
- 비교 그룹 추가/변경
- 완료

---

## Works Well With

- `moai-lang-python` — Python statistical libraries (scipy, pandas, matplotlib)
- `moai-domain-backend` — For integrating analysis results into backend APIs
- `moai-workflow-jit-docs` — For fetching latest scipy/pandas documentation

## Modules

- Questioning Protocol — Edge cases and batch mode
- Test Selection Logic — Statistical test decision tree
- Interpretation Templates — Natural language templates