---

## name: builder-skill description: Cline 스킬을 새로 만들거나 외부 스킬 문서를 Cline 형식으로 변환하는 메타 스킬. 새 스킬 생성, 스킬 구조 설계, 외부 문서 → Cline 형식 변환에 사용. Use when: skill creation, new skill, builder, 스킬생성, 새스킬, 스킬제작, 스킬만들기, convert skill, 스킬변환, cline skill, 스킬 구조, skill structure, skill builder

# Cline 스킬 빌더

## 작업 유형 판단표

이 스킬을 로드한 후 가장 먼저 아래 표에서 작업 유형을 확인하세요.

| 요청 내용 | 이동할 문서 |
| --- | --- |
| 새로운 스킬을 처음부터 만들고 싶다 | `docs/skill-creation-guide.md` |
| 외부 문서를 Cline 스킬로 변환하고 싶다 | `docs/skill-conversion-guide.md` |
| Cline 스킬 형식/규칙을 알고 싶다 | `docs/cline-skill-spec.md` |
| Cline 공식 도구 목록이 필요하다 | `docs/cline-tools-reference.md` |
| 스킬 구조 예시가 필요하다 | `templates/skill-structure.md` |
| SKILL.md 템플릿이 필요하다 | `templates/SKILL.md.template` |

---

## Cline 스킬 핵심 구조 (빠른 참조)

```
.cline/skills/{스킬명}/
├── SKILL.md              ← 진입점 (필수)
├── docs/                 ← 상세 가이드 문서 (선택)
│   └── *.md
├── scripts/              ← 실행 가능한 유틸리티 스크립트 (선택, 프로젝트 규약)
│   └── *.py / *.sh
└── templates/            ← 복사하여 쓰는 템플릿 파일 (선택)
    └── *
```

> **프로젝트 규약**: 이 프로젝트의 스킬은 `docs/` + `scripts/` 구조를 기본으로 사용합니다. `scripts/`에는 Cline이 `execute_command`로 실행하는 Python/Shell 스크립트를 배치합니다. `templates/`는 사용자가 직접 복사하는 보일러플레이트 파일에 사용합니다.

**SKILL.md 필수 형식:**

```
---

## name: {스킬명} description: | {설명}... Use when: {키워드1}, {키워드2}, {키워드3}

# {스킬 제목}

---

## {섹션들...}
```

---

## 새 스킬 생성 빠른 체크리스트

방향을 잃지 않도록 각 단계를 완료 후 체크하세요.

- [ ] 1\. 스킬 목적과 대상 사용자 명확히 정의

- [ ] 2\. 트리거 키워드 10개 이상 작성 (한국어 + 영어)

- [ ] 3\. `templates/SKILL.md.template` 복사하여 SKILL.md 초안 작성

- [ ] 4\. docs/ 문서 필요 여부 판단 (복잡하면 분리)

- [ ] 5\. scripts/ 파일 필요 여부 판단 (실행 스크립트가 있으면 추가)

- [ ] 5-1. templates/ 파일 필요 여부 판단 (복사용 보일러플레이트가 있으면 추가)

- [ ] 6\. 라우팅 테이블 작성 (어떤 요청 → 어떤 문서)

- [ ] **7. 각 Step에 Cline 도구명 명기 확인** (도구 미명기 시 발동 안 됨)

- [ ] 8\. 검증 체크리스트 확인 (`docs/skill-creation-guide.md` Phase 5)

자세한 단계별 가이드: `docs/skill-creation-guide.md`

---

## 도구 명기 규칙 (필수)

> **경고**: Cline은 "사용자에게 질문한다"처럼 자연어만 쓰면 `ask_followup_question` 도구가 발동되지 않을 수 있습니다.

각 Step에서 사용할 Cline 도구를 명시적으로 기재하세요:

| 하려는 작업 | 반드시 포함할 문구 |
| --- | --- |
| 사용자에게 질문 | `ask_followup_question 도구를 사용하여 질문합니다:` |
| 파일 생성 | `write_to_file 도구로 생성합니다:` |
| 파일 읽기 | `read_file 도구로 읽습니다` |
| 파일 수정 | `replace_in_file 도구로 수정합니다` |
| 명령어 실행 | `execute_command 도구로 실행합니다:` |
| 디렉토리 조회 | `list_files 도구로 조회합니다` |
| 내용 검색 | `search_files 도구로 검색합니다` |

도구별 상세 사용법과 예시: `docs/cline-tools-reference.md`

---

## 외부 스킬 변환 빠른 체크리스트

- [ ] 1\. 소스 문서 분석 (어떤 시스템의 스킬인지 파악)

- [ ] 2\. 핵심 지식/패턴 추출

- [ ] 3\. 지원 불가 기능 제거: Hooks, MCP (사내 환경 제약)

- [ ] 4\. Cline 스킬 구조로 매핑

- [ ] 5\. SKILL.md 작성 후 docs/ 구성

- [ ] 6\. 변환 품질 체크리스트 확인

자세한 변환 가이드: `docs/skill-conversion-guide.md`

---

## 사내 환경 제약사항

| 기능 | 상태 | 대안 |
| --- | --- | --- |
| Hooks | 사용 불가 | SKILL.md에 수동 절차 명시 |
| MCP 서버 | 사내망만 가능 | docs/ 폴더에 내용 임베딩 |
| URL 페칭 | `@https://...` 문법 사용 | 접근 불가 시 docs/ 내용 활용 |

---

## 공식 문서 참조

- Cline 스킬: @https://docs.cline.bot/customization/skills
- Cline 커스터마이징 개요: @https://docs.cline.bot/customization/overview
- Cline 워크플로우: @https://docs.cline.bot/customization/workflows
- Cline 공식 도구: @https://docs.cline.bot/tools-reference/all-cline-tools