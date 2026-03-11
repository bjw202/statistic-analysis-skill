# Cline 스킬 변환 가이드

외부 스킬 문서를 Cline 스킬 형식으로 변환하는 가이드입니다.

---

## 지원하는 입력 유형

| 소스 유형 | 특징 | 변환 난이도 |
| --- | --- | --- |
| MoAI-ADK 스킬 (.md) | YAML frontmatter, 구조화된 섹션 | 낮음 |
| 다른 AI 시스템 스킬 | 시스템마다 형식 다름 | 중간 |
| 일반 마크다운 문서 | 비정형 내용 | 중간 |
| 위키/노션 페이지 | 링크, 임베드 포함 | 높음 |
| PDF/Word 문서 | 비마크다운 형식 | 높음 |

---

## 변환 워크플로우

### Step 1: 소스 문서 분석

소스 문서를 읽고 다음 항목을 파악합니다.

**파악할 정보:**
- 이 스킬/문서의 핵심 목적은 무엇인가?
- 어떤 기술/도메인을 다루는가?
- 어떤 구조로 이루어져 있는가?
- 지원 불가 기능이 포함되어 있는가?

**분석 체크리스트:**
- [ ] 핵심 목적 파악
- [ ] 주요 섹션/토픽 목록 작성
- [ ] Hooks 사용 여부 확인
- [ ] MCP 의존성 확인
- [ ] 에이전트 스폰 기능 확인
- [ ] 다른 시스템 특화 기능 확인

### Step 2: 핵심 지식 추출

소스에서 Cline 환경에서도 유효한 내용만 추출합니다.

**추출 대상:**
- 도메인 지식 (기술 개념, 패턴, 규칙)
- 단계별 절차
- 코드 예제
- 설정 파일 예제
- 트러블슈팅 가이드
- API/명령어 참조

**추출 제외 대상:**
- 특정 시스템에서만 동작하는 에이전트 호출
- Hooks 기반 자동화 (사내 환경 제약)
- 사내망 접근 불가 MCP 서버 의존 기능
- 다른 플랫폼 전용 syntax/명령어

### Step 3: Cline 스킬 구조로 매핑

추출한 내용을 Cline 구조에 배치합니다.

| 소스 내용 유형 | Cline 배치 위치 |
| --- | --- |
| 핵심 절차/단계 | SKILL.md 주요 섹션 |
| 상세 가이드 | docs/{topic}.md |
| 코드 예제 | templates/ 또는 docs/examples.md |
| API 참조 | docs/reference.md |
| 설정 예제 | templates/*.example |
| 스크립트/유틸리티 | scripts/ (원본 그대로 복사) |
| 키워드/트리거 | SKILL.md frontmatter Use when |

### Step 3.5: 부수 파일 모두 복사

**소스 스킬에 포함된 docs, scripts, templates 등 모든 파일을 Cline 스킬 폴더에 복사합니다.**

Cline 스킬은 독립적으로 배포되므로, 스킬 실행에 필요한 모든 파일이 `.cline/skills/{스킬명}/` 내부에 있어야 합니다.

```bash
# 소스에 scripts/ 폴더가 있는 경우
cp -r {소스경로}/scripts .cline/skills/{스킬명}/scripts

# 소스에 templates/ 폴더가 있는 경우
cp -r {소스경로}/templates .cline/skills/{스킬명}/templates

# 소스에 docs/ 폴더가 있는 경우
cp -r {소스경로}/docs .cline/skills/{스킬명}/docs
```

복사 후 SKILL.md 및 docs/ 내의 경로 참조를 실제 위치에 맞게 업데이트하세요.

예: `{SCRIPTS_DIR}` 플레이스홀더 → `.cline/skills/{스킬명}/scripts`

### Step 4: 지원 불가 기능 처리

다음 기능을 발견하면 대안으로 교체합니다.

**Hooks → 수동 절차**

원본:
```yaml
# hooks.json (Cline 지원 안 함)
{
  "onFileCreate": "run_script.sh"
}
```

변환:
```markdown
**파일 생성 후 수동으로 수행할 단계:**
1. `run_script.sh` 실행
2. 실행 결과 확인
```

**MCP 서버 → docs/ 임베딩**

원본:
```
# 외부 MCP를 통해 API 문서 조회
```

변환:
```markdown
## API 참조 (임베딩)
<!-- docs/api-reference.md에 API 내용 직접 포함 -->
```

**에이전트 스폰 → 단계별 지침**

원본:
```
Agent(subagent_type="expert-backend", prompt="...")
```

변환:
```markdown
**Step N: 백엔드 구현**
다음 지침에 따라 구현하세요:
- ...
- ...
```

### Step 5: 키워드 Cline 용으로 조정

소스 문서의 키워드를 Cline 사용자 관점으로 재작성합니다.

**원칙:**
- 사용자가 채팅창에 입력할 법한 단어 사용
- 기술 용어와 일상 표현 모두 포함
- 한국어/영어 병행

**예시 (MoAI-ADK → Cline):**

MoAI 키워드: `agent-invocation, subagent, Task(), delegation`
Cline 키워드: `에이전트호출, 작업위임, 자동화, automation, workflow`

### Step 6: SKILL.md + docs/ + templates/ 작성

`docs/skill-creation-guide.md`의 Phase 2-4를 따라 각 파일을 작성합니다.

**MoAI-ADK 환경 주의**: `Write` 도구로 `.cline/skills/` 하위에 SKILL.md를 생성하면 `moai hook post-tool`이 Claude Code 스킬 형식으로 재포맷합니다. `Write` 후 즉시 `Edit`으로 Cline 프론트매터를 재설정하세요.

---

## MoAI-ADK → Cline 변환 특화 가이드

MoAI-ADK 스킬을 Cline으로 변환할 때 자주 만나는 패턴입니다.

### MoAI-ADK YAML frontmatter 처리

MoAI-ADK frontmatter는 풍부한 메타데이터를 포함합니다.

**MoAI-ADK 원본:**
```yaml
---
name: moai-example-skill
version: 1.0.0
description: "This skill does X. Use when Y."
category: domain
allowed-tools: Read, Write, Bash
model: claude-sonnet-4-20250514
tags: [backend, api, rest]
---
```

**Cline 변환:**
```
---
name: example-skill
description: X를 수행하는 스킬. Y 상황에서 사용합니다. Use when: X, Y, {추가 키워드}
---

# Example Skill
```

처리 규칙:
- `name` → 그대로 사용 (또는 한국어 컨텍스트에 맞게 조정)
- `description` → 한국어로 번역 + `Use when:` 섹션 추가
- `version`, `category`, `tags` → 필요 없으면 제거
- `allowed-tools`, `model` → Cline은 지원 안 함, 제거
- `context: fork`, `agent` → 제거

### MoAI-ADK 섹션 구조 매핑

| MoAI-ADK 섹션 | Cline 배치 |
| --- | --- |
| Quick Reference | SKILL.md 상단 |
| Implementation Guide | docs/guide.md 또는 SKILL.md |
| Advanced Patterns | docs/advanced.md |
| Works Well With | SKILL.md 하단 또는 제거 |

### MoAI-ADK 특화 기능 처리

| MoAI 기능 | Cline 대안 |
| --- | --- |
| `Agent()` 호출 | 단계별 지침으로 변환 |
| `Task()`, `TeamCreate()` | 수동 워크플로우 문서화 |
| `AskUserQuestion()` | Cline은 자동으로 처리 |
| hooks.json | 수동 절차 문서화 |
| MCP 서버 | docs/에 내용 임베딩 |
| `/moai` 명령어 | Cline 스킬 트리거 키워드로 대체 |
| context7 라이브러리 조회 | `@https://...` URL 참조로 대체 |

---

## 변환 품질 체크리스트

변환 완료 후 아래 항목을 확인합니다.

### 내용 완전성

- [ ] 소스의 핵심 지식이 모두 보존되었는가?
- [ ] 단계별 절차가 명확한가?
- [ ] 코드 예제가 Cline 환경에서 실행 가능한가?

### Cline 호환성

- [ ] Hooks 관련 내용이 제거/대체되었는가?
- [ ] 외부 MCP 의존성이 제거/대체되었는가?
- [ ] 다른 시스템 전용 문법이 제거되었는가?
- [ ] 에이전트 스폰 코드가 수동 절차로 변환되었는가?

### SKILL.md 품질

- [ ] frontmatter 형식이 올바른가?
- [ ] 한국어 키워드가 포함되어 있는가?
- [ ] 라우팅 테이블이 있는가? (docs/ 파일 있을 경우)
- [ ] 사내 제약사항(Hooks, MCP)이 명시되어 있는가?

### 사용성

- [ ] 처음 보는 사람도 따라할 수 있는가?
- [ ] 방향을 잃을 위험이 없는가?
- [ ] 필요한 정보를 빠르게 찾을 수 있는가?

---

## 변환 예시: MoAI-ADK 스킬 → Cline 스킬

### 원본 (MoAI-ADK 형식)

```
---
name: moai-library-langchain
description: LangChain integration patterns for MoAI workflows.
  Use when: langchain, chains, agents, tool calling, RAG
category: library
allowed-tools: Read, Write, Bash
---

# LangChain Integration

## Quick Reference
...Agent() 호출 패턴...

## Implementation Guide
...context7로 문서 조회...
```

### 변환 결과 (Cline 형식)

```
---
name: langchain-integration
description: LangChain을 프로젝트에 통합하는 스킬. 체인 구성, 에이전트 구축, 도구 호출, RAG 패턴 구현에 사용. Use when: langchain, chains, agent, tool calling, RAG, 랭체인, 에이전트, 도구호출, 벡터검색, 체인구성
---

# LangChain 통합 가이드

---

## 작업 유형 판단표

| 요청 | 이동 |
| --- | --- |
| 기본 체인 구성 | `docs/chains.md` |
| 에이전트 구축 | `docs/agents.md` |
| RAG 구현 | `docs/rag.md` |

...
```
