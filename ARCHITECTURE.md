# statistic-analysis 스킬 아키텍처 문서

> 버전: 1.0.0 | 최종 수정: 2026-03-11

---

## 1. 개요

`statistic-analysis`는 MoAI Claude Code 스킬로, 사용자가 Excel 실험 데이터를 업로드하면 **대화형 질의 → 설정 자동 생성 → 통계 분석 → 대시보드 출력** 파이프라인을 자율적으로 실행한다.

### 핵심 설계 원칙

| 원칙 | 구현 방식 |
|------|-----------|
| **이식성** | 모든 Python 스크립트가 스킬 폴더 내부(`scripts/`)에 위치 |
| **자율성** | 정규성·등분산 검정 결과로 통계 검정을 자동 선택 |
| **투명성** | 각 분석 세트마다 검정 근거를 자연어로 설명 |
| **경로 안정성** | `${CLAUDE_SKILL_DIR}` 변수로 절대 경로 의존성 제거 |

---

## 2. 파일 구조

```
.claude/skills/statistic-analysis/
│
├── SKILL.md                          # 스킬 정의 (YAML frontmatter + 실행 지시문)
│   ├── [Level 1] Quick Reference     # ~100 tokens, 항상 로드
│   └── [Level 2] Execution Directive # ~5000 tokens, 트리거 시 로드
│
├── modules/
│   ├── questioning-protocol.md       # 질의 프로토콜 & 엣지 케이스
│   ├── test-selection-logic.md       # 통계 검정 결정 트리
│   └── interpretation-templates.md  # 자연어 해석 템플릿
│
└── scripts/                          # Python 분석 엔진
    ├── statistic_analyzer.py         # 메인 오케스트레이터 (CLI 진입점)
    ├── data_loader.py                 # Excel 로딩 + 요약 출력
    ├── annotator.py                   # 분석 세트 자동 구성
    ├── analysis_engine.py             # 통계 검정 선택 + 실행
    ├── visualizer.py                  # matplotlib/seaborn 시각화
    ├── reporter.py                    # Markdown 대시보드 조립
    └── requirements.txt               # 의존성 (pandas, scipy, matplotlib...)
```

---

## 3. 전체 실행 흐름

```mermaid
flowchart TD
    USER([사용자]) -->|"/statistic-analysis ftg.xlsx"| CLAUDE[Claude Code]

    CLAUDE --> SKILL[SKILL.md 로드]
    SKILL --> PARSE[Step 1: 인수 파싱\nexcel_path 추출]

    PARSE --> LOADER["Step 2: data_loader.py --summary\n열 목록·통계 요약 출력"]
    LOADER --> PREVIEW[사용자에게 데이터 미리보기 표시]

    PREVIEW --> Q1["Step 3: Phase 1 질의\nQ1.1 실험 설명\nQ1.2 측정값 타입\nQ1.3 컨트롤 열 선택"]

    Q1 --> Q2["Step 4: Phase 2 질의\n열별 조건 어노테이션\nQ2.1~Q2.3 반복"]

    Q2 --> Q3["Step 5: Phase 3 질의\nQ3.1 분석 목적\nQ3.2 유의수준 α\nQ3.3 효과 크기\nQ3.4 출력 경로"]

    Q3 --> CONFIG["Step 6: analysis_config.json 생성\n(Write 도구 사용)"]

    CONFIG --> ENGINE["Step 7: statistic_analyzer.py 실행\n(Bash 도구)"]

    ENGINE --> RESULT["Step 8: 결과 표시\n유의한 비교 목록\n보고서 경로"]

    RESULT --> NEXT["Step 9: 다음 단계 질문\n재분석 / 그룹 변경 / 완료"]

    style USER fill:#4a9eff,color:#fff
    style CLAUDE fill:#7c3aed,color:#fff
    style CONFIG fill:#f59e0b,color:#fff
    style ENGINE fill:#10b981,color:#fff
```

---

## 4. Phase 별 질의 흐름

```mermaid
sequenceDiagram
    participant U as 사용자
    participant C as Claude (SKILL.md)
    participant PY as data_loader.py

    Note over C,PY: Step 2 — 데이터 로드
    C->>PY: python3 data_loader.py ftg.xlsx --summary
    PY-->>C: 열 목록, N, 평균, 표준편차, 결측값 수
    C->>U: 데이터 미리보기 표시

    Note over U,C: Phase 1 — 데이터 개요 (3문항)
    C->>U: Q1.1: 실험을 1-2 문장으로 설명해주세요
    U-->>C: "플렉서블 글라스 벤딩 반지름 측정..."
    C->>U: Q1.2: 측정값 타입? (연속형/비율/이진/모름)
    U-->>C: 연속형 측정값
    C->>U: Q1.3: 컨트롤 열은? [Ref / Cond.1 / ...]
    U-->>C: Ref

    Note over U,C: Phase 2 — 열 어노테이션 (열당 반복)
    loop 각 처리군 열 (Cond.1, Cond.2, ...)
        C->>U: Q2.1: 열 'Cond.1'의 실험 조건은?
        U-->>C: "6μm 에칭, 광학계A"
        C->>U: Q2.2: 여러 요인의 조합인가요?
        U-->>C: 예
        C->>U: Q2.3a: 각 요인을 FactorName=Value 형식으로 입력
        U-->>C: "EtchingDepth=6um\nOpticalSystem=LensA"
    end

    Note over U,C: Phase 3 — 분석 의도 (4문항)
    C->>U: Q3.1: 분석 목적? (컨트롤비교/요인분리/전체/직접)
    U-->>C: 특정 요인의 효과 분리
    C->>U: Q3.2: 유의수준 α? (0.05/0.01/0.10/직접입력)
    U-->>C: 0.05
    C->>U: Q3.3: 효과 크기 지표?
    U-->>C: Cohen's d
    C->>U: Q3.4: 보고서 저장 경로?
    U-->>C: 엑셀 파일과 같은 폴더
```

---

## 5. `annotator.py` — 분석 세트 자동 구성 알고리즘

```mermaid
flowchart TD
    CONFIG[analysis_config.json] --> GOAL{primary_goal?}

    GOAL -->|pairwise_vs_control| PVC["각 처리군 열\nvs 컨트롤 열\n1:1 쌍 생성"]
    GOAL -->|factor_isolation| FI["요인 분리 쌍 탐색\n1개 요인만 다른 쌍 찾기"]
    GOAL -->|full_factorial| FF["모든 C(n,2) 쌍\n완전 조합"]
    GOAL -->|custom| CU["사용자 지정 쌍\nanalysis.custom_comparisons"]

    FI --> ALGO["알고리즘:\nfor each factor F:\n  for each pair (c1, c2):\n    diff = {k | c1.factors[k] ≠ c2.factors[k]}\n    if len(diff) == 1 → 유효한 분리 쌍"]

    ALGO --> EXAMPLE["예시 결과 (ftg.xlsx):\n① Cond.1 vs Cond.2\n   → OpticalSystem 분리 (6μm 고정)\n② Cond.3 vs Cond.4\n   → OpticalSystem 분리 (16μm 고정)\n③ Cond.1 vs Cond.3\n   → EtchingDepth 분리 (LensA 고정)\n④ Cond.2 vs Cond.4\n   → EtchingDepth 분리 (LensB 고정)"]

    PVC --> SETS[분석 세트 목록]
    EXAMPLE --> SETS
    FF --> SETS
    CU --> SETS

    style FI fill:#f59e0b,color:#fff
    style ALGO fill:#fef3c7
    style EXAMPLE fill:#ecfdf5
```

---

## 6. `analysis_engine.py` — 통계 검정 선택 결정 트리

```mermaid
flowchart TD
    START([분석 세트 입력]) --> NORM["Shapiro-Wilk 검정\n각 그룹별 정규성 확인\n(n ≥ 3인 경우만)"]

    NORM --> NC{모든 그룹\n정규분포?}

    NC -->|예| LEV["Levene's 검정\n등분산성 확인"]
    NC -->|아니오| NPAR[비모수 검정 경로]

    LEV --> EV{등분산?}

    EV -->|예 + 2그룹| TTEST["Independent\nt-test\nt, df, p-value"]
    EV -->|아니오 + 2그룹| WELCH["Welch's\nt-test\nt, df, p-value"]
    EV -->|예 + 3그룹+| ANOVA["One-way\nANOVA\n→ Tukey HSD"]
    EV -->|아니오 + 3그룹+| WANOVA["Welch\nANOVA\n→ Games-Howell"]

    NPAR --> NG{그룹 수?}
    NG -->|2그룹| MWU["Mann-Whitney U\n(비모수 t-test 대안)"]
    NG -->|3그룹+| KW["Kruskal-Wallis\n→ Dunn's test\n(사후 검정)"]

    TTEST --> OUT
    WELCH --> OUT
    ANOVA --> OUT
    WANOVA --> OUT
    MWU --> OUT
    KW --> OUT

    OUT["결과 출력:\n- test_name, stat, p_value\n- cohens_d / eta_squared\n- is_significant (p < α)\n- posthoc_df (3그룹+ 시)"] --> VIZ[visualizer.py]

    style TTEST fill:#d1fae5
    style WELCH fill:#d1fae5
    style ANOVA fill:#d1fae5
    style WANOVA fill:#d1fae5
    style MWU fill:#dbeafe
    style KW fill:#dbeafe
    style OUT fill:#7c3aed,color:#fff
```

---

## 7. Python 모듈 데이터 흐름

```mermaid
graph LR
    XLSX[(ftg.xlsx)] --> DL[data_loader.py]
    CFG[(analysis_config.json)] --> AN[annotator.py]

    DL -->|DataFrame| AE[analysis_engine.py]
    AN -->|분석 세트 목록| AE

    AE -->|통계 결과 dict| VIZ[visualizer.py]
    AE -->|통계 결과 dict| REP[reporter.py]

    VIZ -->|PNG bytes\n박스플롯\n히트맵| REP

    REP -->|analysis_report.md\nbase64 PNG 내장| OUT[(보고서 파일)]

    SA[statistic_analyzer.py] -.->|오케스트레이션| DL
    SA -.->|오케스트레이션| AN
    SA -.->|오케스트레이션| AE
    SA -.->|오케스트레이션| VIZ
    SA -.->|오케스트레이션| REP
    SA -->|JSON 요약| CLAUDE[Claude]

    style SA fill:#7c3aed,color:#fff
    style CLAUDE fill:#4a9eff,color:#fff
    style OUT fill:#10b981,color:#fff
```

---

## 8. `visualizer.py` — 박스플롯 생성 로직

```mermaid
flowchart LR
    DATA[그룹별 데이터\nDict] --> BP[seaborn boxplot\n+ strip overlay]

    BP --> ANN{유의한\n비교 쌍?}
    ANN -->|예| BKT["유의성 괄호 추가\np < 0.001 → ***\np < 0.01  → **\np < 0.05  → *\np ≥ 0.05  → ns"]
    ANN -->|아니오| PLAIN[괄호 없음]

    BKT --> PNG[PNG bytes 반환]
    PLAIN --> PNG

    PNG --> B64[base64 인코딩]
    B64 --> MD["Markdown에 삽입\n![plot](data:image/png;base64,...)"]
```

---

## 9. 보고서 (`analysis_report.md`) 구조

```mermaid
graph TD
    RPT[analysis_report.md] --> S1[1. 헤더\n파일명·실험 설명·α값]
    RPT --> S2[2. 분석 요약 테이블\n검정명·p값·유의여부·효과크기]
    RPT --> S3[3. 분석 세트별 상세 결과\n반복: 각 분석 세트]
    RPT --> S4[4. 부록\nanalysis_config.json 전문]

    S3 --> D1[기술 통계 표\nN·평균±SD·중앙값·IQR]
    S3 --> D2[정규성 검정 표\nShapiro-Wilk W·p값]
    S3 --> D3[박스플롯 PNG\nbase64 내장]
    S3 --> D4[검정 결과\n통계량·p값·효과크기]
    S3 --> D5[자연어 해석\n2~3 문장]

    style RPT fill:#f59e0b,color:#fff
```

---

## 10. 자연어 해석 생성 로직

```mermaid
flowchart TD
    RES[통계 결과] --> SIG{p < α?}

    SIG -->|예| S1["'{요인}'은(는) '{측정값}'에\n통계적으로 유의한 영향을 미칩니다\n({검정명}, p={p:.3f})"]
    SIG -->|아니오| S2["통계적으로 유의한 차이가\n발견되지 않았습니다\n({검정명}, p={p:.3f})"]

    S1 --> ES{효과 크기\nCohen's d}
    S2 --> ES

    ES -->|d < 0.2| N1["negligible (무시 가능)"]
    ES -->|0.2 ≤ d < 0.5| N2["small (작은)"]
    ES -->|0.5 ≤ d < 0.8| N3["medium (중간)"]
    ES -->|d ≥ 0.8| N4["large (큰)"]

    N1 --> OUT["최종 해석 문장\n평균·표준편차·% 차이 포함"]
    N2 --> OUT
    N3 --> OUT
    N4 --> OUT
```

---

## 11. 스킬 트리거 조건

SKILL.md의 `triggers` 설정에 따라 Claude가 자동으로 스킬을 로드하는 조건:

```yaml
triggers:
  keywords:
    - statistics, Excel, xlsx
    - ANOVA, t-test, p-value
    - significance, experimental data
    - control group, box plot
    - 유의차, 통계 분석          # 한국어 트리거
  phases: [run]
```

| 트리거 유형 | 예시 |
|------------|------|
| 파일 확장자 | `ftg.xlsx` 언급 |
| 통계 키워드 | "t-test 해줘", "ANOVA 분석" |
| 한국어 키워드 | "유의차 확인", "통계 분석" |
| 직접 호출 | `/statistic-analysis data.xlsx` |

---

## 12. `analysis_config.json` 스키마

스킬이 Claude와 Python 엔진 사이의 **계약(contract)** 으로 사용하는 JSON 구조:

```json
{
  "source": {
    "file_path": "ftg.xlsx",
    "sheet_name": "Data"
  },
  "experiment": {
    "description": "플렉서블 글라스 벤딩 반지름 측정...",
    "response_type": "continuous",
    "control_column": "Ref"
  },
  "columns": {
    "Ref": {
      "role": "control",
      "label": "참조 (컨트롤)",
      "factors": {}
    },
    "Cond.1": {
      "role": "treatment",
      "label": "6μm 에칭, 광학계A",
      "factors": {
        "EtchingDepth": "6um",
        "OpticalSystem": "LensA"
      }
    }
  },
  "analysis": {
    "primary_goal": "factor_isolation",
    "alpha": 0.05,
    "effect_size_metrics": ["cohens_d"],
    "output_dir": ".",
    "analysis_sets": []  // annotator.py가 자동 채움
  }
}
```

---

## 13. 엣지 케이스 처리

| 상황 | 처리 방식 |
|------|-----------|
| n < 3인 그룹 | Shapiro-Wilk 생략, 보수적으로 비모수 검정 선택 |
| 결측값(NaN) | 열별 독립적으로 NaN 제거 후 분석 |
| 비수치형 열 | `data_loader.py`가 자동 감지·경고 후 제외 |
| 열이 10개 이상 | 배치 모드: 표 템플릿으로 일괄 입력 |
| 단일 열 파일 | 컨트롤만 존재 → 분석 세트 0개 → 오류 안내 |
| 그룹 크기 3:1 이상 차이 | `questioning-protocol.md` 경고 출력 |

---

## 14. 의존성 및 환경

```
pandas>=2.0.0       # Excel 로딩, 데이터프레임
scipy>=1.11.0       # 통계 검정 (shapiro, levene, ttest, mannwhitneyu, kruskal)
matplotlib>=3.7.0   # 박스플롯 렌더링
seaborn>=0.13.0     # 시각화 스타일링
openpyxl>=3.1.0     # Excel 파일 파싱
numpy>=1.24.0       # 수치 연산
scikit-posthocs>=0.9.0  # Dunn's test, Games-Howell
```

설치:
```bash
pip install -r .claude/skills/statistic-analysis/scripts/requirements.txt
```

---

*이 문서는 `statistic-analysis` 스킬 v1.0.0을 기준으로 작성되었습니다.*
