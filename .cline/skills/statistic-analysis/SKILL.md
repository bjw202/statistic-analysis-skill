---
name: statistic-analysis
description: Excel 실험 데이터를 대화형으로 통계 분석하는 스킬. 열 어노테이션 가이드, 비교 그룹 자동 구성, 통계 검정 자동 선택(t-test, ANOVA, Kruskal-Wallis), Markdown 대시보드 및 박스플롯 생성. Use when: 통계분석, 엑셀분석, excel analysis, statistics, ANOVA, t-test, p-value, 유의차, 실험데이터, xlsx, 박스플롯, box plot, 통계 검정, 정규성, 분산분석, 실험 조건, 컨트롤 그룹, experimental data, significance, control group, 유의수준, 효과크기, effect size, 요인설계, factorial design
---

# Statistical Analysis Skill

Excel 실험 데이터 분석 — 대화형 컬럼 어노테이션, 비교 그룹 자동 구성, 통계 검정 자동 선택, 대시보드 생성.

사용법: 분석할 Excel 파일 경로와 함께 이 스킬을 호출하세요.

---

## 작업 유형 판단표

| 요청 내용 | 이동할 문서 |
| --- | --- |
| 질문 프로토콜 / 예외 상황 / 배치 모드 | `docs/questioning-protocol.md` |
| 통계 검정 자동 선택 로직 | `docs/test-selection-logic.md` |
| 결과 자연어 해석 템플릿 | `docs/interpretation-templates.md` |

---

## 실행 절차

### Step 1 — 인수 파싱

분석할 Excel 파일 경로를 확인합니다. 경로가 제공되지 않은 경우:

ask_followup_question 도구를 사용하여 질문합니다: "분석할 Excel 파일 경로를 입력해주세요. 선택적으로 `--sheet 시트명` 플래그를 사용할 수 있습니다."

### Step 2 — 데이터 로드 및 미리보기

execute_command 도구로 다음을 실행합니다:
```
python .cline/skills/statistic-analysis/scripts/data_loader.py <excel_path> --summary
```

출력 결과(열 요약)를 사용자에게 표시한 후 다음 단계로 진행합니다.

### Step 3 — Phase 1: 데이터 개요

순서대로 다음 질문을 합니다:

**Q1.1** ask_followup_question 도구를 사용하여 질문합니다: "이 실험을 1-2 문장으로 설명해주세요. 측정하는 것은 무엇이며, 각 열은 무엇을 나타내나요?"

**Q1.2** ask_followup_question 도구를 사용하여 질문합니다: "측정값의 타입은 무엇인가요?" 옵션:
- 연속형 측정값 (권장) — 예: 길이, 강도, 반지름
- 비율/정규화 값 — 예: 퍼센트, 배수
- 이진값 (합격/불합격) — 0 또는 1로 인코딩됨
- 잘 모르겠습니다

**Q1.3** ask_followup_question 도구를 사용하여 질문합니다: "어느 열이 컨트롤/참조 그룹인가요?" (열 이름 목록 + "없음" 옵션 제공)

### Step 4 — Phase 2: 열 어노테이션

컨트롤이 아닌 각 열 C에 대해 순서대로 처리합니다.

> 비컨트롤 열이 10개 이상이면 배치 모드를 사용합니다. 자세한 내용은 `docs/questioning-protocol.md`를 참조하세요.

**Q2.1** ask_followup_question 도구를 사용하여 질문합니다: "열 '{C}' 는 어떤 실험 조건을 나타내나요? 예: '레이저 출력 6μm 에칭'"

**Q2.2** ask_followup_question 도구를 사용하여 질문합니다: "이 열은 여러 독립적 실험 요인의 조합인가요?" 옵션:
- 예 — 예: 에칭 깊이 AND 광학계 같은 복합 요인
- 아니오 — 컨트롤에서 단일 요인만 변경됨

Q2.2가 "예"이면:

**Q2.3a** ask_followup_question 도구를 사용하여 질문합니다: "각 요인과 값을 한 줄씩 입력하세요:\nFactorName=Value\n예:\nEtchingDepth=6um\nOpticalSystem=LensA"

Q2.2가 "아니오"이면:

**Q2.3b** ask_followup_question 도구를 사용하여 질문합니다: "변경된 요인과 값을 입력하세요:\nFactorName=Value\n예: EtchingDepth=6um"

### Step 4.5 — 반복 실험 감지

모든 열 어노테이션 완료 후, 동일한 요인 조합을 가진 열을 자동 감지합니다.

반복 실험이 감지된 경우 사용자에게 표시합니다:
```
반복 실험 감지:
  그룹 A: Cond.1, Cond.2 → 광학계=개선, 에칭량=6
  그룹 B: Cond.3, Cond.4 → 광학계=개선, 에칭량=16
```

ask_followup_question 도구를 사용하여 질문합니다: "동일 조건의 열들이 감지되었습니다. 반복 실험 데이터로 처리하여 풀링(pooling)할까요?" 옵션:
- 예 (권장) — 동일 조건의 데이터를 합쳐서 통계적 검정력을 높입니다
- 아니오 — 각 열을 별도 조건으로 유지합니다

### Step 4.6 — 요인 설계 감지

반복 실험 감지 후, 요인 구조에서 요인 설계를 자동 감지합니다.

요인 설계가 감지된 경우 사용자에게 표시합니다:
```
요인 설계 감지: 2×2
  요인 1: 광학계 → [기존, 개선]
  요인 2: 에칭량 → [6, 16]
```

이 정보는 Step 5의 Q3.1에서 "요인별 영향도 비교"를 자동 권장하고 Two-Way ANOVA를 활성화하는 데 사용됩니다.

### Step 5 — Phase 3: 분석 의도

**Q3.1** ask_followup_question 도구를 사용하여 질문합니다: "이 분석의 주요 목적은 무엇인가요?"

요인 설계 감지 시 (Step 4.6):
- 요인별 영향도 비교 (권장) — Two-Way ANOVA로 각 요인의 주효과와 교호작용 분석. 동시에 컨트롤 대비 개별 조건 비교도 수행
- 컨트롤과의 유의차 확인 — 각 조건을 컨트롤과 개별 비교
- 전체 요인 분석 — 모든 쌍별 비교
- 직접 지정 — 비교할 조합 직접 지정

요인 설계 미감지 시:
- 컨트롤과의 유의차 확인 (권장)
- 특정 요인의 효과 분리
- 전체 요인 분석
- 직접 지정

**Q3.2** ask_followup_question 도구를 사용하여 질문합니다: "유의수준(alpha)은 무엇으로 설정할까요?" 옵션:
- α = 0.05 (권장 — 표준 과학적 기준)
- α = 0.01 (엄격)
- α = 0.10 (탐색적 분석)
- 직접 입력

**Q3.3** ask_followup_question 도구를 사용하여 질문합니다: "효과 크기(effect size) 지표는 무엇으로 보고할까요?"

Q3.1 = "요인별 영향도 비교"이면:
- 편 Eta-squared (편 η²) (권장) — 요인별 설명 분산 비율. 요인 영향도 비교에 최적
- Cohen's d — 개별 쌍 비교에 적합한 효과 크기
- 둘 다 보고 — 요인별 η²와 개별 비교별 Cohen's d 모두 보고
- 효과 크기 없이 p-값만

그 외:
- Cohen's d (권장 — 연속 측정값에 적합)
- Eta-squared (η²) — ANOVA 설계에 적합
- 둘 다 보고
- 효과 크기 없이 p-값만

**Q3.4** ask_followup_question 도구를 사용하여 질문합니다: "분석 보고서를 어디에 저장할까요?" 옵션:
- 입력 엑셀 파일과 같은 폴더 (권장)
- 현재 작업 디렉토리
- 직접 경로 입력
- 저장 없이 터미널에만 출력

### Step 6 — 설정 파일 생성

모든 답변을 조합하여 `analysis_config.json`을 생성합니다.

write_to_file 도구로 `<excel_파일_폴더>/analysis_config.json` 파일을 생성합니다:
```json
{
  "experiment": {
    "description": "Q1.1 답변",
    "measurement_type": "continuous|ratio|binary|unknown",
    "control_column": "Ref"
  },
  "columns": {
    "Ref": {
      "role": "control",
      "label": "Control/Reference",
      "factors": {}
    },
    "Cond.1": {
      "role": "treatment",
      "label": "Q2.1 답변",
      "factors": {"EtchingDepth": "6um"}
    }
  },
  "replicates": {},
  "factorial_design": null,
  "analysis": {
    "primary_goal": "pairwise_vs_control|factor_impact_comparison|factor_isolation|full_factorial|custom",
    "alpha": 0.05,
    "effect_size": "cohens_d|partial_eta_squared|eta_squared|both|none",
    "output_path": "/path/to/output/dir"
  }
}
```

### Step 7 — 분석 실행

execute_command 도구로 다음을 실행합니다:
```
python .cline/skills/statistic-analysis/scripts/statistic_analyzer.py <excel_path> <config_path>
```

종료 코드가 0이 아니면 오류를 표시하고 중단합니다.

### Step 8 — 결과 표시

read_file 도구로 생성된 `analysis_report.md` 파일을 읽습니다.

다음을 표시합니다:
- **factor_impact_comparison**인 경우: 요인 영향도 비교 표, 교호작용 유의성, 쌍별 비교 수
- **기타 의도**: 실행된 분석 세트 수, 유의한 비교 목록 (p < alpha), 전체 보고서 경로

### Step 9 — 다음 단계

ask_followup_question 도구를 사용하여 질문합니다: "다음 작업을 선택하세요:" 옵션:
- 다른 alpha 값으로 재분석
- 비교 그룹 추가/변경
- 완료

---

## 빠른 참조

### 통계 검정 선택 요약

| 검정 | 사용 조건 |
| --- | --- |
| Independent t-test | 2그룹, 정규분포, 등분산 |
| Welch's t-test | 2그룹, 정규분포, 비등분산 또는 샘플 불균등 |
| Mann-Whitney U | 2그룹, 비정규분포 |
| One-way ANOVA | 3+그룹, 정규분포, 등분산 |
| Welch ANOVA | 3+그룹, 정규분포, 비등분산 |
| Kruskal-Wallis | 3+그룹, 비정규분포 |
| Two-Way ANOVA | 2+ 요인, 각 2+ 수준 |

자세한 결정 트리: `docs/test-selection-logic.md`

### 스크립트 목록

| 스크립트 | 용도 |
| --- | --- |
| `scripts/data_loader.py` | Excel 파일 로드 및 열 요약 |
| `scripts/statistic_analyzer.py` | 분석 실행 진입점 |
| `scripts/analysis_engine.py` | 통계 검정 실행 엔진 |
| `scripts/visualizer.py` | 박스플롯 생성 |
| `scripts/reporter.py` | Markdown 보고서 생성 |
| `scripts/annotator.py` | 자연어 해석 생성 |
| `scripts/requirements.txt` | Python 패키지 의존성 |

패키지 설치:
```
pip install -r .cline/skills/statistic-analysis/scripts/requirements.txt
```

---

## 제약사항

| 기능 | 상태 | 대안 |
| --- | --- | --- |
| Hooks | 사내 환경에서 사용 불가 | SKILL.md에 수동 절차 명시 |
| MCP 서버 | 사내망만 접속 가능 | docs/에 내용 임베딩 |

---

## 공식 문서 참조

- scipy 통계 함수: @https://docs.scipy.org/doc/scipy/reference/stats.html
- pandas 문서: @https://pandas.pydata.org/docs/
