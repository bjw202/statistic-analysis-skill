# Cline 공식 도구 참조

Cline이 사용하는 공식 도구 목록입니다. 워크플로우나 스킬을 설계할 때 Cline이 어떤 도구를 사용할 수 있는지 파악하면 더 정확한 지침을 작성할 수 있습니다.

공식 문서: @https://docs.cline.bot/tools-reference/all-cline-tools

---

## 1. 파일 작업 도구

| 도구 | 설명 | 사용 시기 |
| --- | --- | --- |
| `write_to_file` | 파일 생성 또는 전체 덮어쓰기 | 새 파일 생성, 파일 전체 교체 |
| `read_file` | 파일 내용 읽기 | 파일 분석, 내용 파악 |
| `replace_in_file` | 파일 일부만 수정 (정밀 편집) | 기존 파일의 특정 부분만 변경 |
| `search_files` | 정규식으로 파일 내용 검색 | 패턴 찾기, 코드 검색 |
| `list_files` | 디렉토리 목록 조회 | 프로젝트 구조 파악 |
| `list_code_definition_names` | 파일에서 코드 정의 추출 | 함수/클래스 목록 확인 |

---

## 2. 터미널 도구

| 도구 | 설명 | 사용 시기 |
| --- | --- | --- |
| `execute_command` | CLI 명령어 실행 | 빌드, 테스트, 패키지 설치, 스크립트 실행 |

### execute_command 활용 예시

스킬/워크플로우에서 Cline이 명령어를 실행하도록 지시:

```
1. 의존성 설치: `pip install -r requirements.txt` 실행
2. 테스트 실행: `pytest tests/` 실행
3. 스크립트 실행: `python scripts/new-skill.sh {스킬명}` 실행
```

---

## 3. 브라우저 도구

| 도구 | 설명 | 사용 시기 |
| --- | --- | --- |
| `browser_action` | 브라우저 자동화 (Puppeteer) | 웹 스크래핑, UI 테스트, 스크린샷 캡처 |

**사용 가능한 액션:**
- `launch` - 브라우저 시작
- `click` - 요소 클릭
- `type` - 텍스트 입력
- `scroll` - 스크롤
- `screenshot` - 스크린샷
- `close` - 브라우저 종료

**사내 환경 제약**: 브라우저 도구는 사내망 환경에 따라 제한될 수 있습니다.

---

## 4. 사용자 상호작용 도구

| 도구 | 설명 | 사용 시기 |
| --- | --- | --- |
| `ask_followup_question` | 사용자에게 질문 | 필요한 정보가 불명확할 때 |
| `new_task` | 새 컨텍스트로 작업 전환 | 대화가 너무 길어졌을 때 |

---

## 5. MCP 도구

사내망에서 접근 가능한 MCP 서버의 도구를 사용할 수 있습니다.

**사내 환경 제약**: 외부 MCP 서버는 사용 불가합니다. 사내 MCP 서버만 접속 가능합니다.

---

## 6. 워크플로우에서 도구 명시하기

`.clinerules/workflows/` 의 워크플로우 파일에서는 Cline XML 문법으로 도구를 직접 호출할 수 있습니다.

### XML 도구 호출 문법

```xml
<execute_command>
<command>npm install</command>
</execute_command>

<read_file>
<path>src/index.ts</path>
</read_file>

<ask_followup_question>
<question>어떤 스킬명을 사용할까요?</question>
</ask_followup_question>
```

### 스킬(SKILL.md)에서 도구 지시하기

SKILL.md에서는 자연어로 지시하면 Cline이 적합한 도구를 선택합니다.

**좋은 예시 (도구 의도가 명확한 지시):**
```markdown
**Step 1: 디렉토리 구조 확인**
`.cline/skills/` 디렉토리 목록을 조회하여 기존 스킬 목록을 파악합니다.

**Step 2: 스킬 파일 생성**
`.cline/skills/{스킬명}/SKILL.md` 파일을 생성합니다. 내용은 아래 형식을 따릅니다:
[내용...]

**Step 3: 검증**
생성된 파일을 읽어 frontmatter 형식이 올바른지 확인합니다.
```

**나쁜 예시 (도구 의도가 모호한 지시):**
```markdown
스킬을 만드세요.
```

---

## 7. 도구별 스킬 설계 패턴

### 파일 생성 작업

지시 예시:
```markdown
다음 내용으로 `{경로}` 파일을 생성합니다:
[파일 내용]
```

### 기존 파일 수정 작업

지시 예시:
```markdown
`{파일경로}` 파일에서 `{기존 내용}` 부분을 찾아 `{새 내용}`으로 교체합니다.
```

### 명령어 실행 작업

지시 예시:
```markdown
다음 명령어를 실행합니다:
```bash
{명령어}
```
실행 결과를 확인하고 오류가 있으면 수정합니다.
```

### 사용자 입력이 필요한 작업

지시 예시:
```markdown
{필요한 정보}를 사용자에게 질문합니다. 답변을 받은 후 다음 단계를 진행합니다.
```

---

## 참고: Cline vs Claude Code 도구 비교

| 용도 | Cline 도구 | Claude Code 도구 |
| --- | --- | --- |
| 파일 읽기 | `read_file` | `Read` |
| 파일 쓰기 | `write_to_file` | `Write` |
| 파일 수정 | `replace_in_file` | `Edit` |
| 파일 검색 | `search_files` | `Grep` |
| 디렉토리 조회 | `list_files` | `Glob` |
| 명령어 실행 | `execute_command` | `Bash` |
| 사용자 질문 | `ask_followup_question` | `AskUserQuestion` |

스킬 작성 시 혼동하지 않도록 주의하세요. 이 스킬은 Cline용입니다.
