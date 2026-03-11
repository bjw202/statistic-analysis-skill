# Cline 스킬 형식 명세

Cline 스킬의 공식 구조와 규칙을 정의합니다.

---

## 1. 디렉토리 구조

### 기본 구조

```
.cline/skills/{스킬명}/
├── SKILL.md              ← 진입점 (필수)
├── docs/                 ← 상세 가이드 문서 (선택)
│   ├── topic-a.md
│   └── topic-b.md
├── scripts/              ← 실행 가능한 유틸리티 스크립트 (선택)
│   ├── helper.py
│   └── setup.sh
└── templates/            ← 복사하여 쓰는 보일러플레이트 파일 (선택)
    ├── example.py
    └── config.example
```

> **프로젝트 규약**: 이 프로젝트에서는 `docs/` + `scripts/` 구조를 기본으로 사용합니다.
>
> | 폴더 | 내용 | 사용 예 |
> | --- | --- | --- |
> | `scripts/` | Cline이 `execute_command`로 실행하는 스크립트 | `add_slide.py`, `setup.sh` |
> | `templates/` | 사용자가 복사하여 쓰는 파일 | `SKILL.md.template`, `.env.example` |

### 명명 규칙

- 스킬 디렉토리명: `kebab-case` 사용 (예: `builder-skill`, `gauss-langchain-integration`)
- 영문 소문자, 숫자, 하이픈만 허용
- 의미 있는 이름 사용 (도메인-기능 형태 권장)

---

## 2. SKILL.md 파일 형식

### 필수 구조

```
---
name: {스킬명}
description: {스킬 설명 — 무엇을 하는지, 언제 사용하는지}. Use when: {키워드1}, {키워드2}, {키워드3}, ...
---

# {스킬 제목}

---

## {섹션 1}

...내용...

## {섹션 2}

...내용...
```

### frontmatter 규칙

`name` **필드:**

- 스킬 디렉토리명과 일치시키는 것을 권장
- kebab-case

`description` **필드:**

- 한 줄 문자열로 작성 (`|` 블록 스칼라 불필요)
- 스킬이 무엇을 하는지 1-2문장으로 설명
- 마지막에 반드시 `Use when:` 섹션 포함
- `Use when:` 뒤에 트리거 키워드를 쉼표로 나열

`Use when:` **키워드 작성 원칙:**

- 사용자가 실제로 입력할 법한 단어/구문 사용
- 한국어 + 영어 모두 포함 (각 10개 이상 권장)
- 동의어, 축약어, 오탈자 변형 포함 가능
- 예시: `스킬생성, 새스킬, skill creation, new skill, 스킬 만들기`

---

## 3. docs/ 폴더

### 목적

SKILL.md에 담기에 너무 긴 상세 내용을 분리하여 저장합니다.

### 언제 사용하는가

- 특정 주제에 대한 심화 가이드가 필요할 때
- 코드 예제가 많아 SKILL.md가 길어질 때
- 독립적인 하위 주제가 3개 이상일 때

### 파일 명명

- `topic-name.md` 형태 (kebab-case)
- 내용을 명확히 반영하는 이름 사용
- 예: `skill-creation-guide.md`, `api-reference.md`, `troubleshooting.md`

### 콘텐츠 가이드라인

- 각 docs 파일은 하나의 주제에 집중
- 파일 상단에 제목과 간단한 목적 설명 포함
- 단계별 절차는 번호 매긴 목록 사용
- 결정 사항은 표(table)로 정리
- 코드 예제는 언어 명시한 코드 블록 사용

### SKILL.md에서 docs/ 참조 방법

```markdown
자세한 내용은 `docs/topic-name.md`를 참조하세요.
```

Cline은 이 경로를 읽어 해당 파일을 로드합니다.

---

## 4. scripts/ 폴더

### 목적

Cline이 `execute_command`로 실행하는 유틸리티 스크립트를 저장합니다.

### 언제 사용하는가

- 반복 실행이 필요한 자동화 작업이 있을 때
- 복잡한 파일 처리나 변환 로직이 있을 때
- 스킬 사용 시 Cline이 실행해야 할 스크립트가 있을 때

### 파일 유형 예시

- `.py`: Python 유틸리티 스크립트 (예: `add_slide.py`, `new-skill.sh`)
- `.sh`: Shell 스크립트

### 콘텐츠 가이드라인

- 파일 상단에 용도와 사용법 주석 포함 (`# 용도:`, `# 사용법:`)
- 스크립트는 독립 실행 가능하게 작성
- `if __name__ == "__main__":` 패턴 사용 (Python)
- 실행 권한 부여 필요: `chmod +x scripts/*.sh`

### SKILL.md에서 scripts/ 참조 방법

```markdown
**Step 1: 스크립트 실행**
다음 명령어를 실행합니다:
```bash
python .cline/skills/{스킬명}/scripts/helper.py {인수}
```
```

---

## 4-1. templates/ 폴더

### 목적

사용자가 복사하여 바로 사용할 수 있는 파일 템플릿을 저장합니다. `scripts/`와 구분: 실행하는 것은 `scripts/`, 복사하는 것은 `templates/`.

### 언제 사용하는가

- 반복적으로 사용되는 코드 스캐폴딩이 있을 때
- 설정 파일 예제가 필요할 때
- 빠른 시작을 위한 보일러플레이트가 있을 때

### 파일 유형 예시

- `.py`, `.ts`, `.js`: 코드 템플릿
- `.md.template`, `.md`: 마크다운 템플릿
- `.env.example`, `.yaml.example`: 설정 예제

### 콘텐츠 가이드라인

- 파일 상단에 용도와 사용 방법 주석 포함
- 교체 필요한 값은 `{PLACEHOLDER}` 또는 `YOUR_VALUE_HERE` 형태로 표시
- 민감 정보(키, 패스워드)는 절대 실제 값 사용 금지

---

## 5. Cline 공식 도구

Cline이 작업 수행 시 사용하는 공식 도구입니다. 스킬/워크플로우 설계 시 이 도구들을 기반으로 지침을 작성하세요.

자세한 내용: `docs/cline-tools-reference.md`

### 핵심 도구 요약

| 도구 | 용도 |
| --- | --- |
| `execute_command` | CLI 명령어/스크립트 실행 |
| `write_to_file` | 파일 생성 또는 전체 덮어쓰기 |
| `read_file` | 파일 내용 읽기 |
| `replace_in_file` | 파일 일부 수정 |
| `search_files` | 파일 내용 검색 |
| `list_files` | 디렉토리 목록 조회 |
| `browser_action` | 브라우저 자동화 |
| `ask_followup_question` | 사용자에게 질문 |
| `new_task` | 새 컨텍스트로 전환 |

---

## 6. SKILL.md 콘텐츠 모범 사례

### 라우팅 테이블 (필수 권장)

스킬 시작 부분에 작업 유형별 이동 경로를 표로 제공하면 방향 유지에 효과적입니다.

```markdown
## 작업 유형 판단표

| 요청 내용 | 이동할 문서 |
| --- | --- |
| A를 하고 싶다 | `docs/guide-a.md` |
| B를 하고 싶다 | `docs/guide-b.md` |
| 빠른 예제 필요 | `templates/example.py` |
```

### 단계별 가이드

번호 매긴 목록으로 절차를 명확히 합니다.

```markdown
**Step 1: 준비**
- 항목 A 설치
- 항목 B 설정

**Step 2: 실행**
- 명령어 C 실행
```

### 체크리스트

방향을 잃지 않도록 체크리스트를 제공합니다.

```markdown
- [ ] 1. 항목 1 완료
- [ ] 2. 항목 2 완료
- [ ] 3. 항목 3 완료
```

### 제약사항 표

환경 제약이 있을 경우 명확히 표로 정리합니다.

```markdown
| 기능 | 상태 | 대안 |
| --- | --- | --- |
| 기능 A | 사용 불가 | 대안 B 사용 |
| 기능 C | 제한적 | 조건 D일 때만 가능 |
```

---

## 7. 사내 환경 제약사항

이 섹션은 이 프로젝트의 사내 Cline 환경에만 해당됩니다.

### Hooks — 사용 불가

Cline의 Hooks 기능(`hooks.json`)은 사내 환경에서 지원되지 않습니다.

- 대안: SKILL.md에 수동으로 수행할 절차를 명시
- 자동화가 필요한 경우 별도 스크립트를 `templates/`에 포함

### MCP 서버 — 사내망만 접속 가능

MCP 서버는 사내망에서만 접속할 수 있습니다. 외부 MCP 서버는 사용 불가입니다.

- 대안: 필요한 정보를 `docs/` 폴더에 임베딩
- 사내 MCP가 있다면 연결 방법을 스킬에 명시

### URL 페칭 — `@https://...` 문법

Cline은 `@https://example.com` 형태로 URL을 참조할 수 있습니다.

- 공식 문서를 최신 상태로 참조할 때 유용
- 사내망에서 접근 불가한 URL이 있을 수 있음
- 접근 불가 시 대비책으로 `docs/`에 핵심 내용 임베딩 권장

---

## 8. 스킬 품질 기준

완성된 스킬이 충족해야 할 기준입니다.

| 항목 | 기준 |
| --- | --- |
| SKILL.md 존재 | 필수 |
| frontmatter 형식 | name, description, Use when 모두 포함 |
| 키워드 수 | Use when에 10개 이상 |
| 라우팅 테이블 | docs/ 파일이 있으면 반드시 포함 |
| 한국어 지원 | 키워드와 주요 설명에 한국어 포함 |
| 제약사항 명시 | 사내 환경 제약 관련 내용 포함 |
| 단계별 구조 | 복잡한 절차는 번호 매긴 단계로 제공 |
