---
name: statistic-analysis
description: Excel 실험 데이터를 대화형으로 통계 분석하는 스킬. 컬럼 주석, 비교 그룹 자동 구성, 적절한 통계 검정 선택(t-test, ANOVA, Kruskal-Wallis), Markdown 보고서 및 박스플롯 생성을 지원합니다. 회사 DRM 환경(Windows, win32com)에서 동작하도록 설계되어 있습니다. Use when: 통계분석, 실험데이터, Excel분석, xlsx, 유의차, t-test, ANOVA, p-value, 박스플롯, 컨트롤그룹, 처리그룹, 요인분석, 벤딩R, 에칭, statistics, experimental data, significance test, box plot, control group, treatment group, factorial design, two-way anova, effect size, 실험 조건 비교, 데이터분석, data analysis
---

# 통계 분석 스킬 (Statistical Analysis)

Excel 실험 데이터를 대화형으로 분석합니다. 자동으로 적절한 통계 검정을 선택하고, 시각화 및 자연어 해석을 제공합니다.

> **환경**: Windows + Microsoft Excel 설치 필수. 회사 DRM 보안 솔루션에 로그인된 상태에서 실행하세요.

---

## 작업 유형 판단표

| 요청 내용 | 이동할 문서 |
| --- | --- |
| 엣지 케이스, 10개 이상 컬럼 배치 모드 | `docs/questioning-protocol.md` |
| 통계 검정 선택 로직 (정규성, 분산, 검정법) | `docs/test-selection-logic.md` |
| 결과 자연어 해석 템플릿 | `docs/interpretation-templates.md` |

---

## 핵심 절차

### Step 0 — 최초 실행: 의존성 확인

처음 사용하거나 패키지 오류가 발생하면 다음 명령어를 실행합니다:

```bash
pip install -r .cline/skills/statistic-analysis/scripts/requirements.txt
```

실행 후 오류가 없으면 Step 1로 진행합니다.

> **win32com 관련**: `pip install pywin32` 실패 시, 관리자 권한으로 명령 프롬프트를 열고 재시도하세요. `pywintypes` import 오류가 발생하면 `scripts/data_loader.py` 상단 주석의 `[TROUBLESHOOT-1]`을 참고하세요.

---

### Step 1 — 파일 경로 파싱

사용자 메시지에서 Excel 파일 경로를 추출합니다.

- 경로가 없으면 사용자에게 질문합니다: "분석할 Excel 파일 경로를 알려주세요."
- `--sheet SHEET_NAME` 플래그가 있으면 추출합니다 (기본값: "Data" 시트 → 없으면 첫 번째 시트)

---

### Step 2 — 데이터 로드 및 미리보기

다음 명령어를 실행합니다:

```bash
python3 .cline/skills/statistic-analysis/scripts/data_loader.py <excel_path> --summary
```

실행 결과(컬럼 요약, 행 수, 결측값 현황)를 사용자에게 보여줍니다. 오류 발생 시:
- `com_error`: 회사 보안 솔루션에 로그인되었는지 확인하도록 안내합니다.
- `FileNotFoundError`: 파일 경로가 올바른지 확인합니다.
- 그 외: `scripts/data_loader.py` 상단의 `[TROUBLESHOOT-*]` 주석을 참고합니다.

---

### Step 3 — Phase 1: 데이터 개요

컬럼 요약을 보여준 뒤 순서대로 질문합니다.

**Q1.1**: "이 실험을 1-2 문장으로 설명해주세요. 측정하는 것은 무엇이며, 각 열은 무엇을 나타내나요?"

**Q1.2**: "측정값의 타입은 무엇인가요?"
- 연속형 측정값 (권장) — 예: 길이, 강도, 반지름
- 비율/정규화 값 — 예: 퍼센트, 배수
- 이진값 (합격/불합격) — 0 또는 1로 인코딩됨
- 잘 모르겠습니다

**Q1.3**: "어느 열이 컨트롤/참조 그룹인가요?" (데이터에서 읽은 컬럼명 목록을 선택지로 제시)

---

### Step 4 — Phase 2: 컬럼 주석

비컨트롤 컬럼 C 각각에 대해 하나씩 처리합니다.

> 비컨트롤 컬럼이 10개 이상이면 배치 모드를 사용합니다 → `docs/questioning-protocol.md` 참조

**Q2.1**: "열 '{C}' 는 어떤 실험 조건을 나타내나요? (예: '개선 광학계, 에칭량 6')"

**Q2.2**: "이 열은 여러 독립적 실험 요인의 조합인가요?"
- 예 — 예: 에칭 깊이 AND 광학계 같은 복합 요인
- 아니오 — 컨트롤에서 단일 요인만 변경됨

"예"이면 **Q2.3a**: "각 요인과 값을 한 줄씩 입력하세요 (FactorName=Value 형식):"
```
EtchingDepth=6um
OpticalSystem=LensA
```

"아니오"이면 **Q2.3b**: "변경된 요인과 값을 입력하세요 (FactorName=Value 형식):"
```
EtchingDepth=6um
```

---

### Step 4.5 — 반복 실험 감지

모든 컬럼 주석 완료 후, 동일한 요인 조합을 가진 컬럼을 자동으로 탐지합니다.

**알고리즘**: 비컨트롤 컬럼을 요인 딕셔너리로 그룹화. 2개 이상이 동일한 요인이면 반복 실험입니다.

감지 시 사용자에게 표시합니다:
```
반복 실험 감지:
  그룹 A: Cond.1, Cond.2 → 광학계=개선, 에칭량=6
  그룹 B: Cond.3, Cond.4 → 광학계=개선, 에칭량=16
```

**Q_REP**: "동일 조건의 열들이 감지되었습니다. 반복 실험 데이터로 처리하여 풀링(pooling)할까요?"
- 예 (권장) — 동일 조건의 데이터를 합쳐서 통계적 검정력을 높입니다
- 아니오 — 각 열을 별도 조건으로 유지합니다

---

### Step 4.6 — 요인 설계 감지

반복 실험 감지 후, 요인 구조에서 요인 설계를 자동 감지합니다.

**알고리즘**: 모든 컬럼(컨트롤 포함)의 요인명과 고유 수준을 수집. 요인이 2개 이상이고 각각 2개 이상 수준이면 요인 설계입니다.

감지 시 사용자에게 표시합니다:
```
요인 설계 감지: 2×2
  요인 1: 광학계 → [기존, 개선]
  요인 2: 에칭량 → [6, 16]
```

---

### Step 5 — Phase 3: 분석 의도

**Q3.1**: "이 분석의 주요 목적은 무엇인가요?"

요인 설계가 감지된 경우:
- 요인별 영향도 비교 (권장) — Two-Way ANOVA로 각 요인의 주효과와 교호작용을 분석하고, 어떤 요인이 더 큰 영향을 미치는지 비교합니다
- 컨트롤과의 유의차 확인 — 각 조건을 컨트롤과 개별 비교합니다
- 전체 요인 분석 — 모든 쌍별 비교를 수행합니다
- 직접 지정 — 비교할 조합을 직접 지정합니다

요인 설계가 감지되지 않은 경우:
- 컨트롤과의 유의차 확인 (권장) — 각 조건을 컨트롤과 비교합니다
- 특정 요인의 효과 분리 — 하나의 요인만 다른 조건 쌍을 비교합니다
- 전체 요인 분석 — 모든 쌍별 비교를 수행합니다
- 직접 지정 — 비교할 조합을 직접 지정합니다

**Q3.2**: "유의수준(alpha)은 무엇으로 설정할까요?"
- α = 0.05 (권장 — 표준 과학적 기준)
- α = 0.01 (엄격)
- α = 0.10 (탐색적 분석)
- 직접 입력

**Q3.3**: "효과 크기(effect size) 지표는 무엇으로 보고할까요?"

Q3.1이 "요인별 영향도 비교"인 경우:
- 편 Eta-squared (편 η²) (권장) — 요인별 설명 분산 비율. 요인 영향도 비교에 최적
- Cohen's d — 개별 쌍 비교에 적합한 효과 크기
- 둘 다 보고 — 요인별 η²와 개별 비교별 Cohen's d 모두 보고
- 효과 크기 없이 p-값만

그 외:
- Cohen's d (권장 — 연속 측정값에 적합)
- Eta-squared (η²) — ANOVA 설계에 적합
- 둘 다 보고
- 효과 크기 없이 p-값만

**Q3.4**: "분석 보고서를 어디에 저장할까요?"
- 입력 엑셀 파일과 같은 폴더 (권장)
- 현재 작업 디렉토리
- 직접 경로 입력
- 저장 없이 터미널에만 출력

---

### Step 6 — 설정 파일 생성

수집된 모든 답변을 조합하여 `analysis_config.json` 파일을 Excel 파일과 같은 디렉토리에 생성합니다.

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

---

### Step 7 — 분석 실행

다음 명령어를 실행합니다:

```bash
python3 .cline/skills/statistic-analysis/scripts/statistic_analyzer.py <excel_path> <config_path>
```

실행 결과를 확인합니다:
- 종료 코드 0: 정상. stdout의 JSON 결과를 파싱합니다.
- 종료 코드 1 이상: 오류 메시지를 사용자에게 보여주고 중단합니다.

---

### Step 8 — 결과 표시

생성된 `analysis_report.md` 파일을 읽어 다음 항목을 요약하여 표시합니다:

**요인별 영향도 비교인 경우:**
- 요인 영향도 비교 테이블 (Cohen's d 또는 η² 기준 어느 요인이 더 큰 효과인지)
- 교호작용 유의성 여부
- 유의한 쌍별 비교 수

**그 외:**
- 총 분석 세트 수
- 유의한 비교 목록 (p < alpha)

전체 보고서 파일 경로를 안내합니다.

---

### Step 9 — 다음 작업

사용자에게 다음 중 선택을 요청합니다:
- 다른 alpha 값으로 재분석 → Step 5부터 재진행
- 비교 그룹 추가/변경 → Step 4부터 재진행
- 완료

---

## 빠른 참조

| 항목 | 값 |
| --- | --- |
| 스크립트 디렉토리 | `.cline/skills/statistic-analysis/scripts/` |
| 데이터 로더 실행 | `python3 scripts/data_loader.py <excel> --summary` |
| 분석 실행 | `python3 scripts/statistic_analyzer.py <excel> <config>` |
| 설정 파일명 | `analysis_config.json` (Excel과 같은 폴더) |
| 보고서 출력명 | `analysis_report.md` |
| Excel 읽기 방식 | win32com (DRM 대응) → pandas fallback (비Windows) |
| 의존성 설치 | `pip install -r scripts/requirements.txt` |

---

## 실행 체크리스트

- [ ] 0. 의존성 설치 확인 (최초 1회)
- [ ] 1. Excel 파일 경로 확인 및 데이터 로드 (`data_loader.py --summary`)
- [ ] 2. 실험 설명, 측정 타입, 컨트롤 컬럼 확인 (Q1.1~1.3)
- [ ] 3. 각 조건 컬럼 요인 주석 완료 (Q2.1~2.3)
- [ ] 4. 반복 실험 및 요인 설계 자동 감지
- [ ] 5. 분석 의도, 유의수준, 효과 크기 확인 (Q3.1~3.4)
- [ ] 6. `analysis_config.json` 생성
- [ ] 7. `statistic_analyzer.py` 실행 및 오류 확인
- [ ] 8. `analysis_report.md` 읽어 결과 요약 표시

---

## 제약사항

| 기능 | 상태 | 대안 |
| --- | --- | --- |
| Hooks | 사내 환경에서 사용 불가 | SKILL.md 절차 직접 수행 |
| MCP 서버 | 사내망만 접속 가능 | 스크립트 로컬 실행 |
| pandas Excel 직접 읽기 | DRM 파일에서 차단됨 | win32com (data_loader.py 내장) |
| 비Windows 환경 | win32com 사용 불가 | pandas fallback 자동 전환 |

---

## 공식 문서 참조

- scipy 통계 함수: @https://docs.scipy.org/doc/scipy/reference/stats.html
- pandas 데이터프레임: @https://pandas.pydata.org/docs/
- pywin32 (win32com): @https://pypi.org/project/pywin32/
