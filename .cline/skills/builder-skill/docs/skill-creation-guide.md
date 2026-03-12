# Cline 스킬 생성 가이드

새로운 Cline 스킬을 처음부터 만드는 단계별 가이드입니다. 각 Phase를 순서대로 진행하세요.

---

## Phase 1: 기획

### 1-1. 스킬 목적 정의

아래 질문에 답하여 스킬의 범위를 명확히 합니다.

- 이 스킬은 무엇을 도와주는가?
- 주요 대상 사용자는 누구인가?
- 이 스킬 없이는 어떤 불편이 있는가?
- 다른 스킬과 어떻게 구별되는가?

**예시 답변 (builder-skill 기준):**

> 이 스킬은 Cline 스킬을 새로 만들거나 변환할 때 안내한다. 스킬을 처음 만드는 개발자가 대상이며, 방향을 잃지 않도록 체계적인 절차를 제공한다.

### 1-2. 키워드 목록 작성

사용자가 이 스킬을 필요로 할 때 입력할 법한 단어와 구문을 모두 작성합니다.

**필수 포함:**

- 핵심 동작 키워드 (한국어 + 영어)
- 도메인/기술 키워드
- 동의어와 유사 표현

**예시:**

```
스킬생성, 새스킬, 스킬제작, 스킬만들기, 스킬 구조,
skill creation, new skill, builder, create skill,
cline skill, 스킬변환, convert skill, skill builder
```

### 1-3. 파일 구조 계획

아래 표를 채워 스킬 구조를 미리 설계합니다.

| 파일/폴더 | 필요 여부 | 내용 요약 |
| --- | --- | --- |
| SKILL.md | 필수 | 진입점, 라우팅, 핵심 절차 |
| docs/guide.md | 복잡한 경우 | 상세 단계별 가이드 |
| docs/reference.md | API/규칙 있을 경우 | 형식 명세, 제약사항 |
| scripts/helper.py | 실행 스크립트 있을 경우 | Cline이 execute_command로 실행하는 스크립트 |
| templates/example | 복사용 보일러플레이트 있을 경우 | 사용자가 직접 복사하는 파일 |

---

## Phase 2: SKILL.md 작성

### 2-1. frontmatter 작성

`templates/SKILL.md.template`을 복사하여 시작합니다.

frontmatter는 정확한 형식을 따라야 합니다.

```
---
name: {스킬명}
description: {스킬 설명 — 무엇을 하는지 간략히}. Use when: {키워드1}, {키워드2}, {키워드3}
---

# {스킬 제목}
```

**주의사항:**

- `---`는 반드시 맨 첫 줄에 위치
- `name:`, `description:` 은 표준 YAML 형식 (`##` 없음, `|` 없음)
- `description:` 값은 한 줄 문자열로 작성
- `Use when:` 은 `description` 값 끝에 이어서 키워드를 쉼표로 나열
- frontmatter 닫기 `---` 다음에 빈 줄 추가

**Claude Code 스킬과 Cline 스킬의 프론트매터 형식 차이:**

| 구분 | 경로 | 프론트매터 형식 |
| --- | --- | --- |
| Claude Code 스킬 | `.claude/skills/` | `moai hook post-tool`이 관리하는 전용 형식 |
| Cline 스킬 | `.cline/skills/` | 표준 YAML (`---\nname: ...\ndescription: ...\n---`) |

MoAI-ADK 환경에서 `Write` 도구로 `.cline/skills/` 하위에 SKILL.md를 생성하면 `moai hook post-tool`이 Claude Code 스킬 형식으로 재포맷합니다. Cline 스킬에는 이 형식이 맞지 않습니다.

**해결책**: `Write` 후 즉시 `Edit` 도구로 프론트매터를 올바른 Cline 형식으로 재설정하세요. (`Edit`은 차이(diff)만 처리하므로 훅의 전체 재포맷이 적용되지 않음)

### 2-2. 라우팅 테이블 작성

SKILL.md 상단(제목 바로 아래)에 라우팅 테이블을 배치합니다.

```markdown
## 작업 유형 판단표

| 요청 내용 | 이동할 문서 |
| --- | --- |
| A를 하고 싶다 | `docs/guide-a.md` |
| B를 하고 싶다 | `docs/guide-b.md` |
| 빠른 예제 필요 | `templates/example.py` |
```

**라우팅 테이블 설계 원칙:**

- 사용자가 할 법한 요청을 2-5개 유형으로 분류
- 각 유형에 대응하는 문서를 정확히 명시
- 문서가 하나뿐이라면 라우팅 테이블 생략 가능

### 2-3. 주요 섹션 작성

라우팅 테이블 아래에 다음 섹션을 필요에 따라 추가합니다.

**빠른 참조 섹션** (선택):

- 핵심 명령어, API, 구조 등 즉시 필요한 정보
- 코드 블록이나 표로 간결하게 제공

**단계별 가이드 섹션** (선택):

- 주요 작업 흐름을 순서대로 제시
- 각 단계는 명확한 액션으로 구성

**제약사항 섹션** (환경 제약이 있을 경우):

- 사용 불가 기능과 대안 명시
- 표 형태로 정리

### 2-4. 흔한 실수 (안티패턴)

| 안티패턴 | 문제점 | 올바른 방법 |
| --- | --- | --- |
| SKILL.md에 모든 내용 몰아넣기 | 너무 길어져 방향 상실 | docs/로 분리하고 라우팅 |
| 키워드 없이 설명만 작성 | 스킬이 발동되지 않음 | Use when에 키워드 충분히 포함 |
| 절차 없이 정보만 나열 | Cline이 무엇을 해야 할지 모름 | 명확한 단계(Step 1, 2, 3) 제공 |
| 제약사항 미명시 | 불가능한 방법을 시도하게 됨 | 제약과 대안을 명확히 표기 |
| 영어 키워드만 작성 | 한국어 요청 시 발동 안 됨 | 한국어 키워드 반드시 포함 |
| **도구 이름 미명기** | **도구가 발동되지 않음** | **각 Step에 Cline 도구명 명시** |

---

## Phase 2-5: 도구 명기 규칙 (필수)

> **핵심 규칙**: Cline은 자연어만으로는 도구를 발동하지 않을 수 있습니다. 각 Step에서 사용할 도구를 반드시 명시하세요.

### 잘못된 작성 vs 올바른 작성

**사용자 질문**
```markdown
❌ 잘못된 예:
사용자에게 스킬명을 물어봅니다.

✅ 올바른 예:
ask_followup_question 도구를 사용하여 사용자에게 질문합니다:
"새로 만들 스킬의 이름은 무엇인가요? (kebab-case로 입력)"
```

**파일 생성**
```markdown
❌ 잘못된 예:
SKILL.md를 만들어라.

✅ 올바른 예:
write_to_file 도구로 `.cline/skills/{스킬명}/SKILL.md`를 생성합니다.
내용:
---
name: {스킬명}
...
```

**파일 읽기**
```markdown
❌ 잘못된 예:
기존 파일을 확인합니다.

✅ 올바른 예:
read_file 도구로 `{경로}` 파일을 읽어 내용을 확인합니다.
```

**명령어 실행**
```markdown
❌ 잘못된 예:
패키지를 설치합니다.

✅ 올바른 예:
execute_command 도구로 다음을 실행합니다:
pip install -r requirements.txt
```

**디렉토리 조회**
```markdown
❌ 잘못된 예:
기존 스킬 목록을 확인합니다.

✅ 올바른 예:
list_files 도구로 `.cline/skills/` 디렉토리를 조회하여
기존 스킬 목록을 확인합니다.
```

### 도구 명기 체크리스트

각 Step을 작성한 후 아래를 확인하세요:

- [ ] 파일을 읽는 Step → `read_file 도구로` 명시되어 있는가?
- [ ] 파일을 생성하는 Step → `write_to_file 도구로` 명시되어 있는가?
- [ ] 파일을 수정하는 Step → `replace_in_file 도구로` 명시되어 있는가?
- [ ] 명령어 실행 Step → `execute_command 도구로` 명시되어 있는가?
- [ ] 사용자 질문 Step → `ask_followup_question 도구를 사용하여` 명시되어 있는가?
- [ ] 디렉토리 조회 Step → `list_files 도구로` 명시되어 있는가?
- [ ] 내용 검색 Step → `search_files 도구로` 명시되어 있는가?

도구별 상세 사용법: `docs/cline-tools-reference.md`

---

## Phase 3: docs/ 작성

### 3-1. 분리 기준

다음 조건 중 하나라도 해당하면 docs/로 분리합니다.

- SKILL.md가 100줄을 넘을 것 같을 때
- 특정 주제에 대한 심화 내용이 필요할 때
- 독립적인 하위 주제가 3개 이상일 때
- 자주 업데이트될 내용이 있을 때

### 3-2. docs 파일 구조

각 docs 파일은 다음 구조를 따릅니다.

```markdown
# {파일 제목}

{이 문서의 목적 — 1-2문장}

---

## {주요 섹션 1}

{내용}

## {주요 섹션 2}

{내용}
```

### 3-3. 권장 docs 파일 유형

| 파일명 패턴 | 내용 유형 |
| --- | --- |
| `*-guide.md` | 단계별 작업 가이드 |
| `*-spec.md` | 형식 명세, 규칙 |
| `*-reference.md` | API, 명령어 참조 |
| `*-examples.md` | 코드/구성 예제 모음 |
| `troubleshooting.md` | 문제 해결 가이드 |

---

## Phase 4: scripts/ 작성

### 4-1. 포함 기준

다음 조건에 해당하면 scripts/에 파일을 추가합니다.

- Cline이 `execute_command`로 실행해야 하는 스크립트
- 반복 실행이 필요한 자동화 작업
- 복잡한 파일 처리나 변환 로직

**`scripts/` vs `templates/` 구분:**

| 구분 | 내용 | 사내 예시 |
| --- | --- | --- |
| `scripts/` | Cline이 실행하는 스크립트 | `add_slide.py`, `new-skill.sh` |
| `templates/` | 사용자가 복사하는 파일 | `SKILL.md.template`, `.env.example` |

### 4-2. 파일 작성 규칙

```python
# scripts/helper.py
# 용도: {이 스크립트의 목적}
# 사용법: python scripts/helper.py {인수}
#
# 인수:
# - {ARG_A}: {설명}

import sys

def main():
    # ... 실제 로직 ...
    pass

if __name__ == "__main__":
    main()
```

```bash
#!/bin/bash
# scripts/setup.sh
# 용도: {이 스크립트의 목적}
# 사용법: bash scripts/setup.sh {인수}

set -e
# ... 실제 로직 ...
```

### 4-3. SKILL.md에서 scripts/ 참조

```markdown
**Step N: 스크립트 실행**
다음 명령어를 실행합니다:
```bash
python .cline/skills/{스킬명}/scripts/helper.py {인수}
```
실행 결과를 확인하고 오류가 있으면 수정합니다.
```

---

## Phase 4-1: templates/ 작성 (선택)

templates/는 사용자가 직접 복사하여 쓰는 보일러플레이트 파일에 사용합니다.

### 파일 작성 규칙

```python
# templates/example.py
# 용도: {이 파일의 목적}
# 사용법: {어떻게 사용하는지 한 줄 설명}
#
# 교체 필요한 값:
# - {PLACEHOLDER_A}: {설명}
# - {PLACEHOLDER_B}: {설명}

# ... 실제 코드 ...
```

---

## Phase 5: 검증 체크리스트

완성 전에 아래 항목을 모두 확인합니다.

### SKILL.md 검증

- [ ] frontmatter 형식이 정확한가? (`---`로 열고 닫힘, `name:` / `description:` 한 줄 문자열, `|` 없음)

- [ ] `Use when:` 키워드가 10개 이상인가?

- [ ] 한국어 키워드가 포함되어 있는가?

- [ ] 라우팅 테이블이 존재하는가? (docs/ 파일이 있을 경우)

- [ ] 단계별 절차가 명확한가?

- [ ] 제약사항이 명시되어 있는가? (있다면)

### docs/ 검증

- [ ] 각 파일이 하나의 주제에 집중하는가?

- [ ] SKILL.md에서 올바른 경로로 참조되는가?

- [ ] 파일명이 내용을 명확히 반영하는가?

### scripts/ 검증

- [ ] 파일 상단에 용도와 사용법 주석이 있는가?

- [ ] 스크립트가 독립 실행 가능한가?

- [ ] 실행 권한이 부여되었는가? (`.sh` 파일의 경우 `chmod +x`)

- [ ] SKILL.md에서 올바른 실행 경로로 참조되는가?

### templates/ 검증 (해당 시)

- [ ] 파일 상단에 용도 주석이 있는가?

- [ ] 교체 필요한 값이 명확히 표시되어 있는가?

- [ ] 민감 정보(실제 키, 패스워드)가 없는가?

### 전체 구조 검증

- [ ] `.cline/skills/{스킬명}/` 경로가 올바른가?

- [ ] SKILL.md 파일이 존재하는가?

- [ ] 불필요한 파일이 없는가?

---

## 빠른 시작 명령어 시퀀스

새 스킬 생성 시 실행할 명령어 순서입니다.

**방법 1: 스크립트 사용 (권장)**

```bash
# builder-skill 스크립트로 표준 구조 자동 생성
bash .cline/skills/builder-skill/scripts/new-skill.sh {스킬명}
```

**방법 2: 수동 생성**

```bash
# 1. 디렉토리 생성 (프로젝트 규약: docs + scripts)
mkdir -p .cline/skills/{스킬명}/docs
mkdir -p .cline/skills/{스킬명}/scripts

# 필요한 경우 templates/ 추가
mkdir -p .cline/skills/{스킬명}/templates

# 2. SKILL.md 템플릿 복사 (이 스킬의 templates에서)
cp .cline/skills/builder-skill/templates/SKILL.md.template \
   .cline/skills/{스킬명}/SKILL.md

# 3. 내용 작성 시작
```