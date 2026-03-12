# Cline 공식 도구 참조

Cline이 사용하는 모든 공식 도구의 완전한 참조 문서입니다.

---

## 사용 컨텍스트별 도구 호출 방식

Cline에는 두 가지 사용 컨텍스트가 있으며, 각각 도구 호출 방식이 다릅니다.

| 컨텍스트 | 파일 위치 | 도구 호출 방식 |
| --- | --- | --- |
| **스킬** (SKILL.md) | `.cline/skills/` | 자연어 지시 + 도구 이름 명기 |
| **워크플로우** | `.clinerules/workflows/` | XML 태그 직접 삽입 가능 |

### SKILL.md에서 도구 호출

SKILL.md에서는 자연어로 지시하되 **반드시 도구 이름을 명기**합니다. "사용자에게 질문한다"처럼 도구명이 없으면 발동되지 않을 수 있습니다.

```markdown
✅ SKILL.md 올바른 패턴:
ask_followup_question 도구를 사용하여 사용자에게 질문합니다:
"어떤 스킬명을 사용할까요?"

write_to_file 도구로 `src/components/Header.tsx` 파일을 생성합니다:
[내용]
```

### 워크플로우에서 도구 호출

`.clinerules/workflows/` 파일에서는 XML 태그를 직접 삽입할 수 있습니다.

```xml
<write_to_file>
<path>src/components/Header.tsx</path>
<content>
import React from "react"
// ...
</content>
</write_to_file>
```

---

## 도구 완전 참조 (XML 스키마 포함)

### 1. write_to_file — 파일 생성/덮어쓰기

**파일 전체를 생성하거나 덮어씁니다.** 일부 수정은 `replace_in_file` 사용.

**XML 스키마 (워크플로우용)**:

```xml
<write_to_file>
<path>대상 파일 경로</path>
<content>
파일 전체 내용 (비워두면 빈 파일 생성)
</content>
</write_to_file>
```

**실제 예시 (워크플로우)**:

```xml
<write_to_file>
<path>src/components/Header.tsx</path>
<content>
import React from "react"

interface HeaderProps {
  title: string
}

export default function Header({ title }: HeaderProps) {
  return (
    <header style={{ padding: "1rem", borderBottom: "1px solid #eee" }}>
      <h1>{title}</h1>
    </header>
  )
}
</content>
</write_to_file>
```

**SKILL.md 지시 패턴**:

```markdown
write_to_file 도구로 `src/components/Header.tsx` 파일을 생성합니다.
내용은 다음과 같습니다:
```tsx
import React from "react"
// ...
```

```

---

### 2. read_file — 파일 읽기

**파일 내용을 읽습니다.**

**XML 스키마 (워크플로우용)**:
```xml
<read_file>
<path>읽을 파일 경로</path>
</read_file>
```

**실제 예시**:

```xml
<read_file>
<path>.cline/skills/builder-skill/SKILL.md</path>
</read_file>
```

**SKILL.md 지시 패턴**:

```markdown
read_file 도구로 `{경로}` 파일을 읽어 현재 내용을 확인합니다.
```

---

### 3. replace_in_file — 파일 부분 수정

**파일의 특정 부분만 수정합니다.** 전체 덮어쓰기가 아닌 정밀 편집.

**XML 스키마 (워크플로우용)**:

```xml
<replace_in_file>
<path>수정할 파일 경로</path>
<diff>
<<<<<<< SEARCH
기존 내용 (정확히 일치해야 함)
=======
새 내용
>>>>>>> REPLACE
</diff>
</replace_in_file>
```

**실제 예시**:

```xml
<replace_in_file>
<path>src/App.tsx</path>
<diff>
<<<<<<< SEARCH
const title = "Old Title"
=======
const title = "New Title"
>>>>>>> REPLACE
</diff>
</replace_in_file>
```

**SKILL.md 지시 패턴**:

```markdown
replace_in_file 도구로 `src/App.tsx` 파일을 수정합니다.
변경 전: `const title = "Old Title"`
변경 후: `const title = "New Title"`
```

---

### 4. execute_command — 명령어 실행

**CLI 명령어를 실행합니다.**

**XML 스키마 (워크플로우용)**:

```xml
<execute_command>
<command>실행할 명령어</command>
</execute_command>
```

**실제 예시**:

```xml
<execute_command>
<command>npm install</command>
</execute_command>

<execute_command>
<command>python .cline/skills/builder-skill/scripts/new-skill.sh my-new-skill</command>
</execute_command>
```

**SKILL.md 지시 패턴**:

```markdown
execute_command 도구로 다음을 실행합니다:
npm install
실행 완료 후 오류가 없으면 다음 단계로 진행합니다.
```

---

### 5. search_files — 파일 내용 검색

**정규식으로 파일 내용을 검색합니다.**

**XML 스키마 (워크플로우용)**:

```xml
<search_files>
<path>검색 범위 경로</path>
<regex>정규식 패턴</regex>
<file_pattern>파일 패턴 (선택, 예: *.ts)</file_pattern>
</search_files>
```

**실제 예시**:

```xml
<search_files>
<path>.cline/skills</path>
<regex>Use when:</regex>
<file_pattern>SKILL.md</file_pattern>
</search_files>
```

**SKILL.md 지시 패턴**:

```markdown
search_files 도구로 `.cline/skills/` 경로에서
`Use when:` 패턴을 `SKILL.md` 파일에서 검색합니다.
```

---

### 6. list_files — 디렉토리 목록 조회

**디렉토리의 파일/서브디렉토리 목록을 조회합니다.**

**XML 스키마 (워크플로우용)**:

```xml
<list_files>
<path>조회할 경로</path>
<recursive>true 또는 false (기본: false)</recursive>
</list_files>
```

**실제 예시**:

```xml
<list_files>
<path>.cline/skills</path>
<recursive>false</recursive>
</list_files>
```

**SKILL.md 지시 패턴**:

```markdown
list_files 도구로 `.cline/skills/` 디렉토리를 조회하여
기존 스킬 목록을 확인합니다.
```

---

### 7. list_code_definition_names — 코드 정의 추출

**파일에서 함수, 클래스, 메서드 이름을 추출합니다.**

**XML 스키마 (워크플로우용)**:

```xml
<list_code_definition_names>
<path>분석할 파일 또는 디렉토리 경로</path>
</list_code_definition_names>
```

**실제 예시**:

```xml
<list_code_definition_names>
<path>src/utils.py</path>
</list_code_definition_names>
```

**SKILL.md 지시 패턴**:

```markdown
list_code_definition_names 도구로 `src/utils.py`를 분석하여
정의된 함수와 클래스 목록을 파악합니다.
```

---

### 8. ask_followup_question — 사용자에게 질문

**사용자에게 질문하여 추가 정보를 수집합니다.**

> **중요**: SKILL.md에서 "사용자에게 질문한다"처럼 도구명이 없으면 발동 안 됨. 반드시 `ask_followup_question` 명기.

**XML 스키마 (워크플로우용)**:

```xml
<ask_followup_question>
<question>사용자에게 할 질문 내용</question>
<follow_up>
<suggest>선택지 1</suggest>
<suggest>선택지 2</suggest>
<suggest>선택지 3</suggest>
</follow_up>
</ask_followup_question>
```

**실제 예시**:

```xml
<ask_followup_question>
<question>어떤 스킬명을 사용할까요? (kebab-case로 입력)</question>
<follow_up>
<suggest>my-new-skill</suggest>
<suggest>직접 입력하겠습니다</suggest>
</follow_up>
</ask_followup_question>
```

**SKILL.md 지시 패턴**:

```markdown
ask_followup_question 도구를 사용하여 사용자에게 질문합니다:
질문: "어떤 스킬명을 사용할까요? (kebab-case)"
선택지: ["my-api-skill", "my-data-skill", "직접 입력"]

답변을 받은 후 {스킬명} 변수에 저장하고 다음 단계를 진행합니다.
```

---

### 9. browser_action — 브라우저 자동화

**Puppeteer를 통한 브라우저 자동화입니다.**

**XML 스키마 (워크플로우용)**:

```xml
<!-- 브라우저 시작 -->
<browser_action>
<action>launch</action>
<url>https://example.com</url>
</browser_action>

<!-- 요소 클릭 -->
<browser_action>
<action>click</action>
<coordinate>x좌표,y좌표</coordinate>
</browser_action>

<!-- 텍스트 입력 -->
<browser_action>
<action>type</action>
<text>입력할 텍스트</text>
</browser_action>

<!-- 스크린샷 -->
<browser_action>
<action>screenshot</action>
</browser_action>

<!-- 브라우저 종료 -->
<browser_action>
<action>close</action>
</browser_action>
```

**SKILL.md 지시 패턴**:

```markdown
browser_action launch로 `https://example.com`을 엽니다.
페이지 로딩 후 browser_action screenshot으로 현재 화면을 캡처합니다.
작업 완료 후 browser_action close로 브라우저를 종료합니다.
```

**사내 환경 제약**: 외부 URL 접근이 사내망에서 차단될 수 있습니다.

---

### 10. new_task — 새 컨텍스트 전환

**대화가 너무 길어졌을 때 핵심 정보만 가지고 새 작업을 시작합니다.**

**XML 스키마 (워크플로우용)**:

```xml
<new_task>
<context>
새 작업에 전달할 핵심 컨텍스트 내용
</context>
</new_task>
```

**SKILL.md 지시 패턴**:

```markdown
컨텍스트가 너무 길어졌다면 new_task 도구를 사용하여 새 컨텍스트로 전환합니다.
전달할 컨텍스트: "현재까지 {완료된 작업}. 다음으로 {남은 작업}을 진행해야 합니다."
```

---

## 도구 선택 빠른 가이드

| 하려는 작업 | 도구 | SKILL.md 발동 보장 문구 |
| --- | --- | --- |
| 새 파일 만들기 | `write_to_file` | `write_to_file 도구로 \`{경로}\` 파일을 생성합니다:\` |
| 파일 읽기 | `read_file` | `read_file 도구로 \`{경로}\` 파일을 읽습니다\` |
| 파일 일부 수정 | `replace_in_file` | `replace_in_file 도구로 \`{경로}\` 파일을 수정합니다\` |
| 명령어 실행 | `execute_command` | `execute_command 도구로 다음을 실행합니다:` |
| 디렉토리 조회 | `list_files` | `list_files 도구로 \`{경로}\`를 조회합니다\` |
| 내용 검색 | `search_files` | `search_files 도구로 \`{패턴}\`을 검색합니다\` |
| 사용자 질문 | `ask_followup_question` | `ask_followup_question 도구를 사용하여 질문합니다: "{질문}"` |
| 브라우저 열기 | `browser_action` | `browser_action launch로 \`{URL}\`을 엽니다\` |

---

## Cline vs Claude Code 도구 대조표

| 작업 | Cline 도구 | Claude Code 도구 |
| --- | --- | --- |
| 파일 읽기 | `read_file` | `Read` |
| 파일 쓰기 | `write_to_file` | `Write` |
| 파일 수정 | `replace_in_file` | `Edit` |
| 파일 검색 | `search_files` | `Grep` |
| 디렉토리 조회 | `list_files` | `Glob` |
| 명령어 실행 | `execute_command` | `Bash` |
| 사용자 질문 | `ask_followup_question` | `AskUserQuestion` |

> **주의**: 이 스킬은 Cline 환경용입니다. Claude Code 도구명을 Cline 스킬에 사용하면 동작하지 않습니다.