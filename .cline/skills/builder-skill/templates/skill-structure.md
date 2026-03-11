# Cline 스킬 표준 디렉토리 구조

새 스킬을 만들 때 참고하는 구조 레퍼런스입니다.

---

## 기본 구조 (단순 스킬)

단일 주제이거나 내용이 간단할 때 사용합니다.

```
.cline/skills/{스킬명}/
└── SKILL.md              ← 모든 내용을 담은 단일 파일
```

**사용 시기:**
- 절차가 5단계 이하로 간단할 때
- docs/ 분리 없이 SKILL.md 한 파일로 충분할 때

---

## 표준 구조 (중간 복잡도)

대부분의 스킬에 권장하는 구조입니다.

```
.cline/skills/{스킬명}/
├── SKILL.md              ← 진입점: 라우팅, 핵심 절차, 빠른 참조
└── docs/
    ├── guide.md          ← 주요 작업 단계별 가이드
    └── reference.md      ← API/형식/규칙 참조
```

**사용 시기:**
- SKILL.md에 담기에는 내용이 많을 때
- 독립적인 주제가 2-3개 있을 때

---

## 완전 구조 (복잡한 스킬)

다양한 주제와 실행 스크립트, 재사용 가능한 파일이 필요할 때 사용합니다.

```
.cline/skills/{스킬명}/
├── SKILL.md                    ← 진입점 (라우팅 테이블 필수)
├── docs/
│   ├── overview.md             ← 개요 및 핵심 개념
│   ├── getting-started.md      ← 시작 가이드
│   ├── topic-a.md              ← 주제별 상세 가이드
│   ├── topic-b.md
│   ├── advanced.md             ← 고급 패턴 및 엣지케이스
│   ├── troubleshooting.md      ← 문제 해결 가이드
│   └── reference.md            ← API/명령어/형식 참조
├── scripts/                    ← Cline이 execute_command로 실행하는 스크립트
│   ├── main-script.py          ← 주요 유틸리티 스크립트
│   └── setup.sh                ← 환경 설정 스크립트
└── templates/                  ← 사용자가 복사하여 쓰는 보일러플레이트
    ├── main-template.py        ← 주요 코드 템플릿
    ├── config.example.yaml     ← 설정 파일 예제
    └── .env.example            ← 환경변수 예제
```

**사용 시기:**
- 독립적인 주제가 4개 이상일 때
- Cline이 실행해야 할 스크립트가 있을 때
- 사용자가 직접 복사하여 사용할 파일이 있을 때

> **프로젝트 규약**: `docs/` + `scripts/` 조합을 기본으로 사용하세요. `templates/`는 복사용 보일러플레이트가 있을 때만 추가합니다.

---

## 실제 예시: gauss-langchain-integration

이 프로젝트에 존재하는 실제 스킬 구조입니다.

```
.cline/skills/gauss-langchain-integration/
├── SKILL.md
├── docs/
│   ├── langchain-basics.md
│   ├── gauss-wrapper.md
│   ├── react-agent.md
│   ├── langgraph-agent.md
│   ├── tools-catalog.md
│   └── mcp-integration.md
└── templates/
    ├── gauss_llm.py
    ├── react_agent.py
    ├── tools.py
    ├── prompts.py
    └── .env.example
```

---

## 각 파일 역할 설명

### SKILL.md

- **역할**: 스킬의 진입점. Cline이 스킬을 발동할 때 처음 읽는 파일
- **포함 내용**: frontmatter, 라우팅 테이블, 핵심 절차, 빠른 참조
- **길이**: 50-150줄 권장 (너무 길면 docs/로 분리)

### docs/guide.md (또는 주제별 이름)

- **역할**: 특정 작업의 상세 단계별 가이드
- **포함 내용**: 전제 조건, 단계별 절차, 예제, 주의사항
- **길이**: 제한 없음

### docs/reference.md

- **역할**: 빠른 조회가 필요한 참조 정보
- **포함 내용**: API 목록, 명령어 표, 형식 명세
- **특징**: 설명보다 표/목록 위주

### docs/troubleshooting.md

- **역할**: 자주 발생하는 오류와 해결 방법
- **포함 내용**: 증상 → 원인 → 해결책 형태
- **특징**: 검색하기 쉽게 오류 메시지 포함

### scripts/*.py / *.sh

- **역할**: Cline이 `execute_command`로 실행하는 유틸리티 스크립트
- **포함 내용**: 자동화 스크립트, 파일 처리 유틸리티
- **주의**: 독립 실행 가능하게 작성, `chmod +x` 필요 (`.sh`)

### templates/*.py / *.yaml / *.example

- **역할**: 복사하여 바로 사용할 수 있는 파일
- **포함 내용**: 보일러플레이트 코드, 설정 예제
- **주의**: 실제 키/패스워드 절대 포함 금지

---

## SKILL.md → docs/ 분리 판단 기준

| 상황 | SKILL.md에 유지 | docs/로 분리 |
| --- | --- | --- |
| 절차 단계 수 | 1-5단계 | 6단계 이상 |
| 예상 줄 수 | 100줄 이하 | 100줄 초과 |
| 주제 수 | 1-2개 | 3개 이상 |
| 업데이트 빈도 | 드물다 | 자주 변경됨 |
