---
name: statistic-analysis
description: Excel 실험 데이터를 대화형으로 통계 분석하는 스킬. 컬럼 주석, 비교 그룹 자동 구성, 적절한 통계 검정 선택(t-test, ANOVA, Kruskal-Wallis), Markdown 보고서 및 박스플롯 생성을 지원합니다. Use when: 통계분석, 실험데이터, Excel분석, xlsx, 유의차, t-test, ANOVA, p-value, 박스플롯, 컨트롤그룹, 처리그룹, 요인분석, statistics, experimental data, significance test, box plot, control group, treatment group, factorial design, two-way anova, effect size, 통계 검정, 벤딩R, 에칭, 실험 조건 비교
---

# 통계 분석 스킬 (Statistical Analysis)

Excel 실험 데이터를 대화형으로 분석합니다. 자동으로 적절한 통계 검정을 선택하고, 시각화 및 자연어 해석을 제공합니다.

---

## 작업 유형 판단표

| 요청 내용 | 이동할 문서 |
| --- | --- |
| 엣지 케이스, 배치 모드 | `docs/questioning-protocol.md` |
| 통계 검정 선택 로직 | `docs/test-selection-logic.md` |
| 결과 해석 템플릿 | `docs/interpretation-templates.md` |

---

## 핵심 절차

### Step 1 — 파일 경로 파싱

사용자 메시지에서 Excel 파일 경로를 추출합니다.
- 경로가 없으면: "분석할 Excel 파일 경로를 알려주세요."라고 질문합니다.
- `--sheet SHEET_NAME` 플래그 옵션 추출 (기본값: "Data" 또는 첫 번째 시트)

### Step 2 — 데이터 로드 및 미리보기

다음 명령어를 실행하고 결과를 사용자에게 표시합니다:

```bash
python3 .cline/skills/statistic-analysis/scripts/data_loader.py <excel_path> --summary
```

질문 전에 반드시 컬럼 요약 출력을 먼저 보여줍니다.

### Step 3 — Phase 1: 데이터 개요

순서대로 다음 질문을 합니다:

**Q1.1** (자유 텍스트): "이 실험을 1-2 문장으로 설명해주세요. 측정하는 것은 무엇이며, 각 열은 무엇을 나타내나요?"

**Q1.2** (4지선다): "측정값의 타입은 무엇인가요?"
- 연속형 측정값 (권장) — 예: 길이, 강도, 반지름
- 비율/정규화 값 — 예: 퍼센트, 배수
- 이진값 (합격/불합격) — 0 또는 1로 인코딩됨
- 잘 모르겠습니다

**Q1.3** (동적 선택, 옵션 = 컬럼명 + "없음"): "어느 열이 컨트롤/참조 그룹인가요?"

### Step 4 — Phase 2: 컬럼 주석

비컨트롤 컬럼 C 각각에 대해 (하나씩 처리):

**Q2.1** (자유 텍스트): "열 '{C}' 는 어떤 실험 조건을 나타내나요? 예: '레이저 출력 6μm 에칭'"

**Q2.2** (2지선다): "이 열은 여러 독립적 실험 요인의 조합인가요?"
- 예 — 예: 에칭 깊이 AND 광학계 같은 복합 요인
- 아니오 — 컨트롤에서 단일 요인만 변경됨

"예"이면 **Q2.3a**: "각 요인과 값을 한 줄씩 입력하세요:\nFactorName=Value\n예:\nEtchingDepth=6um\nOpticalSystem=LensA"

"아니오"이면 **Q2.3b**: "변경된 요인과 값을 입력하세요:\nFactorName=Value\n예: EtchingDepth=6um"

> 비컨트롤 컬럼이 10개 이상이면 배치 모드 사용: `docs/questioning-protocol.md` 참조

### Step 4.5 — 반복 실험 감지

모든 컬럼 주석 완료 후 동일한 요인 조합을 자동 감지합니다.

**알고리즘**: 비컨트롤 컬럼을 요인 딕셔너리로 그룹화. 2개 이상 컬럼이 동일한 요인을 가지면 반복 실험입니다.

감지 시 사용자에게 표시:
```
반복 실험 감지:
  그룹 A: Cond.1, Cond.2 → 광학계=개선, 에칭량=6
  그룹 B: Cond.3, Cond.4 → 광학계=개선, 에칭량=16
```

**Q_REP**: "동일 조건의 열들이 감지되었습니다. 반복 실험 데이터로 처리하여 풀링(pooling)할까요?"
- 예 (권장) — 동일 조건의 데이터를 합쳐서 통계적 검정력을 높입니다
- 아니오 — 각 열을 별도 조건으로 유지합니다

### Step 4.6 — 요인 설계 감지

반복 실험 감지 후, 요인 구조에서 요인 설계를 자동 감지합니다.

**알고리즘**: 모든 컬럼(컨트롤 포함)에서 요인명과 고유 수준을 수집. 2개 이상 요인이 각각 2개 이상 수준을 가지면 요인 설계입니다.

감지 시 사용자에게 표시:
```
요인 설계 감지: 2×2
  요인 1: 광학계 → [기존, 개선]
  요인 2: 에칭량 → [6, 16]
```

### Step 5 — Phase 3: 분석 의도

**Q3.1** (4지선다, 컨텍스트 기반):

요인 설계 감지 시 (Step 4.6):
- 요인별 영향도 비교 (권장) — Two-Way ANOVA로 각 요인의 주효과와 교호작용 분석
- 컨트롤과의 유의차 확인 — 각 조건을 컨트롤과 개별 비교
- 전체 요인 분석 — 모든 쌍별 비교
- 직접 지정 — 비교할 조합을 직접 지정

요인 설계 미감지 시:
- 컨트롤과의 유의차 확인 (권장)
- 특정 요인의 효과 분리
- 전체 요인 분석
- 직접 지정

**Q3.2** (4지선다): "유의수준(alpha)은 무엇으로 설정할까요?"
- α = 0.05 (권장 — 표준 과학적 기준)
- α = 0.01 (엄격)
- α = 0.10 (탐색적 분석)
- 직접 입력

**Q3.3** (4지선다, 컨텍스트 기반): "효과 크기(effect size) 지표는 무엇으로 보고할까요?"

Q3.1 = "요인별 영향도 비교"인 경우:
- 편 Eta-squared (편 η²) (권장)
- Cohen's d
- 둘 다 보고
- 효과 크기 없이 p-값만

그 외:
- Cohen's d (권장)
- Eta-squared (η²)
- 둘 다 보고
- 효과 크기 없이 p-값만

**Q3.4** (4지선다): "분석 보고서를 어디에 저장할까요?"
- 입력 엑셀 파일과 같은 폴더 (권장)
- 현재 작업 디렉토리
- 직접 경로 입력
- 저장 없이 터미널에만 출력

### Step 6 — 설정 파일 생성

수집된 답변으로 `analysis_config.json`을 작성합니다. Excel 파일과 같은 디렉토리에 저장.

스키마:
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
      "factors": { "광학계": "기존", "에칭량": "6" }
    },
    "Cond.1": {
      "role": "treatment",
      "label": "Q2.1 답변",
      "factors": { "광학계": "개선", "에칭량": "6" }
    }
  },
  "replicates": {
    "group_1": ["Cond.1", "Cond.2"],
    "group_2": ["Cond.3", "Cond.4"]
  },
  "factorial_design": {
    "factors": { "광학계": ["기존", "개선"], "에칭량": ["6", "16"] },
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

### Step 7 — 분석 실행

```bash
python3 .cline/skills/statistic-analysis/scripts/statistic_analyzer.py <excel_path> <config_path>
```

stdout을 캡처합니다. 종료 코드가 0이 아니면 오류를 표시하고 중단합니다.

### Step 8 — 결과 표시

생성된 `analysis_report.md`를 읽어 표시합니다:

- **요인별 영향도 비교**: 요인 영향도 비교 테이블, 교호작용 유의성, 쌍별 비교 수
- **그 외**: 분석 세트 수, 유의한 비교 목록 (p < alpha)
- 전체 보고서 경로

### Step 9 — 다음 작업

다음 중 선택을 요청합니다:
- 다른 alpha 값으로 재분석
- 비교 그룹 추가/변경
- 완료

---

## 빠른 참조

| 항목 | 값 |
| --- | --- |
| 스크립트 경로 | `.cline/skills/statistic-analysis/scripts/` |
| 데이터 로더 | `scripts/data_loader.py <excel> --summary` |
| 분석 실행 | `scripts/statistic_analyzer.py <excel> <config>` |
| 설정 파일 | `analysis_config.json` (Excel 파일과 같은 폴더) |
| 보고서 출력 | `analysis_report.md` |

---

## 실행 체크리스트

- [ ] 1. Excel 파일 경로 확인 및 데이터 로드
- [ ] 2. 실험 설명, 측정 타입, 컨트롤 컬럼 확인 (Q1.1~1.3)
- [ ] 3. 각 조건 컬럼 요인 주석 완료 (Q2.1~2.3)
- [ ] 4. 반복 실험 및 요인 설계 자동 감지
- [ ] 5. 분석 의도, 유의수준, 효과 크기 확인 (Q3.1~3.4)
- [ ] 6. `analysis_config.json` 생성
- [ ] 7. 분석 스크립트 실행
- [ ] 8. 결과 요약 표시 및 보고서 경로 안내

---

## 제약사항

| 기능 | 상태 | 대안 |
| --- | --- | --- |
| Hooks | 사내 환경에서 사용 불가 | SKILL.md 절차 직접 수행 |
| MCP 서버 | 사내망만 접속 가능 | 스크립트 로컬 실행 |
| 자동 AskUserQuestion | Cline 환경에서 직접 처리 | 텍스트로 사용자에게 질문 |

---

## 공식 문서 참조

- scipy 통계 함수: @https://docs.scipy.org/doc/scipy/reference/stats.html
- pandas 데이터프레임: @https://pandas.pydata.org/docs/
