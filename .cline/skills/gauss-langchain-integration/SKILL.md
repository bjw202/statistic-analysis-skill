---
name: gauss-langchain-integration 
description: Gauss LLM을 LangChain/LangGraph에 통합하는 스킬. Gauss 커스텀 LLM 래핑, ReAct 에이전트 구축, LangGraph StateGraph 패턴, MCP 어댑터 연동, 일반 도구(Python 실행, 셸, 웹 검색 등) 구현에 사용. Gauss는 이 환경에서 유일하게 사용하는 LLM이며, 네이티브 tool_call을 지원하지 않아 ReAct 프롬프트 텍스트 파싱 방식을 사용합니다. Use when: gauss, langchain, langgraph, react agent, tool calling, custom llm, mcp adapter, 가우스, 랭체인, 랭그래프, 에이전트, 도구호출, 도구 호출, 커스텀 LLM
---

# Gauss + LangChain/LangGraph 통합 가이드

## 모든 작업의 시작점: Gauss 3단계 필수 절차

**이 스킬의 모든 코드는 Gauss LLM만 사용합니다**.LangChain/LangGraph 작업을 시작하기 전에 반드시 아래 순서를 따르세요.

**Step 1: ChatGauss 래퍼 준비** (항상 먼저)

- `templates/gauss_llm.py`를 프로젝트에 복사

- `templates/.env.example`을 `.env`로 복사 후 실제 값 입력:

  ```
  cp templates/.env.example .env
  ```

- 환경변수 5개 필수 설정: `GAUSS_ENDPOINT`, `GAUSS_CLIENT_KEY`, `GAUSS_PASS_KEY`, `GAUSS_EMAIL`, `GAUSS_MODEL_ID`

- `.env`는 절대 git 커밋 금지 — `.gitignore`에 추가

```python
from gauss_llm import ChatGauss
llm = ChatGauss.from_env()  # 모든 LangChain 코드에서 이 llm을 사용
```

**Step 2: 도구 정의** (도구 사용 시)

- `@tool` 데코레이터로 정의 (`docs/langchain-basics.md` 5번 섹션)
- 또는 `templates/tools.py`에서 기본 도구 복사

**Step 3: 에이전트 조립** (목적에 따라 선택)

- ReAct 방식 (간단한 도구 호출): `templates/react_agent.py` 또는 `docs/react-agent.md`
- LangGraph 방식 (복잡한 흐름 제어): `docs/langgraph-agent.md`

**Gauss 필수 제약 - 절대 사용 불가:**

- `llm.bind_tools(tools)` → 미지원
- `ToolNode` (LangGraph prebuilt) → 미지원
- `create_react_agent` (langgraph.prebuilt) → 미지원
- `create_tool_calling_agent` → 미지원

**대신**: ReAct 프롬프트 텍스트 파싱 방식만 사용 (`docs/react-agent.md`)

---

## 핵심 제약사항

- **Gauss는 네이티브** `tool_call`**을 지원하지 않음** → `bind_tools()`, `create_tool_calling_agent()` 사용 불가
- **해결책**: ReAct 프롬프트 기반 도구 호출 (텍스트 파싱) 또는 LangGraph 커스텀 그래프
- **사내망 주의**: 외부 URL 접근이 제한될 수 있음. 아래 @URL 참조가 로드되지 않으면 docs/ 임베딩 내용을 사용

## 공식 문서 참조 (@URL)

최신 API 확인이 필요할 때 아래 URL을 `@`로 참조하세요. 사내망에서 접근 불가 시 docs/ 폴더의 임베딩 내용을 대신 사용합니다.

- **LangChain 모델 통합**: @https://docs.langchain.com/oss/python/langchain/models
- **LangChain 도구**: @https://docs.langchain.com/oss/python/langchain/tools
- **LangChain MCP 연동**: @https://docs.langchain.com/oss/python/langchain/mcp
- **LangGraph 에이전트**: @https://docs.langchain.com/oss/python/langgraph/workflows-agents
- **LangGraph 퀵스타트**: @https://docs.langchain.com/oss/python/langgraph/quickstart
- **langchain-mcp-adapters**: @https://github.com/langchain-ai/langchain-mcp-adapters

## Gauss API 요약

| 항목 | 값 |
| --- | --- |
| 엔드포인트 | `{ENDPOINT}/openapi/chat/v1/messages` (POST) |
| 모델 목록 | `{ENDPOINT}/openapi/chat/v1/models` (GET) |
| 인증 헤더 | `x-generative-ai-client`, `x-openapi-token`, `x-generative-ai-user-email` |
| 요청 본문 | `modelIds`(array), `contents`(list\[str\]), `llmConfig`, `isStream`, `systemPrompt` |
| 응답 | `content`(답변), `status`, `responseCode` |
| 스트리밍 | SSE, `event_status: "CHUNK"`, `content` 필드로 청크 수신 |

### llmConfig 파라미터

```python
{
    "max_new_tokens": 2024,
    "seed": None,
    "top_k": 14,
    "top_p": 0.94,
    "temperature": 0.4,
    "repetition_penalty": 1.04
}
```

## 환경변수

```bash
export GAUSS_ENDPOINT="http://gauss-internal.company.com"
export GAUSS_CLIENT_KEY="your-client-key"
export GAUSS_PASS_KEY="your-pass-key"
export GAUSS_EMAIL="user@company.com"
export GAUSS_MODEL_ID="model-id-from-api"
```

## 의존성

```bash
# 필수
pip install langchain langchain-core langgraph requests

# 선택 (사용하는 기능에 따라)
pip install beautifulsoup4          # web_fetch HTML 파싱
pip install duckduckgo-search       # web_search
pip install langchain-mcp-adapters  # MCP 연동
pip install sseclient-py            # Gauss 스트리밍
```

## 접근 방식 선택 가이드

## 키워드 기반 라우팅 - 이 키워드가 있으면 해당 문서를 먼저 읽으세요

| 키워드 / 상황 | 참조 문서 |
| --- | --- |
| `import`, `패키지`, `ImportError`, `from langchain`, `langchain_core`, `langgraph` | `docs/langchain-basics.md` |
| `BaseChatModel`, `invoke`, `stream`, `batch`, LCEL, 파이프 문법, 체인 조합 | `docs/langchain-basics.md` |
| `@tool`, `StructuredTool`, `BaseTool`, 도구 정의, tool decorator | `docs/langchain-basics.md` |
| `StrOutputParser`, `JsonOutputParser`, `PydanticOutputParser`, output parser | `docs/langchain-basics.md` |
| `HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage`, 메시지 타입 | `docs/langchain-basics.md` |
| `StateGraph`, `add_node`, `add_edge`, `add_conditional_edges`, `START`, `END` | `docs/langchain-basics.md` + `docs/langgraph-agent.md` |
| `MemorySaver`, `checkpointer`, `thread_id`, 대화 기록, 세션 유지 | `docs/langchain-basics.md` |
| `ConversationBufferMemory`, `LLMChain`, 구버전 API 마이그레이션 | `docs/langchain-basics.md` 7번 섹션 |
| ReAct 에이전트, `create_react_agent`, 텍스트 파싱, 도구 호출 에이전트 | `docs/react-agent.md` |
| LangGraph 커스텀 그래프, 복잡한 워크플로우, 조건부 분기, 멀티 에이전트 | `docs/langgraph-agent.md` |
| 도구 여러 개 조합, 일반 도구 + 외부 도구 통합, 통합 에이전트, `MultiServerMCPClient` | `docs/mcp-integration.md` |
| MCP 서버 연동, `langchain-mcp-adapters`, `MCPClient`, MCP 프로토콜 | `docs/mcp-integration.md` |
| 도구 카탈로그, 파이썬 실행, 웹 검색, 파일 읽기, 셸 명령 도구 | `docs/tools-catalog.md` |
| `ChatGauss`, 래퍼 구현, Gauss API, `_generate`, `_stream`, 헤더, `llmConfig` | `docs/gauss-wrapper.md` |
| Gauss 에이전트 만들기, 도구 연결, 도구 붙이기, 에이전트 구축, tool 추가 | `docs/gauss-wrapper.md` 먼저 → `docs/react-agent.md` |
| 처음 시작, 빠른 시작, 시작하는 방법, 전체 예시, 완성된 코드 | `templates/` 폴더의 py 파일 복사해서 사용 |

## 접근 방식 선택 가이드

| 요구사항 | 추천 방식 | 참조 문서 |
| --- | --- | --- |
| LangChain 기초 / import / LCEL 문법 | **기초 레퍼런스** | `docs/langchain-basics.md` |
| 간단한 도구 호출 에이전트 | **ReAct Agent** (create_react_agent) | `docs/react-agent.md` |
| 복잡한 워크플로우, 상태 관리 | **LangGraph StateGraph** | `docs/langgraph-agent.md` |
| MCP 서버 도구 연동 | **MCP Adapter + ReAct** | `docs/mcp-integration.md` |
| 다양한 일반 도구 사용 | **도구 카탈로그** 참조 | `docs/tools-catalog.md` |

## 구현 순서 (권장)

1. **ChatGauss 래퍼 구현** → `docs/gauss-wrapper.md` 또는 `templates/gauss_llm.py` 복사
2. **도구 정의** → `docs/tools-catalog.md` 또는 `templates/tools.py` 복사
3. **에이전트 조립** → `docs/react-agent.md` 또는 `templates/react_agent.py` 복사
4. (선택) **LangGraph 고급 패턴** → `docs/langgraph-agent.md`
5. (선택) **MCP 도구 통합** → `docs/mcp-integration.md`

## 핵심 주의사항

1. **contents는 문자열 리스트**: Gauss API의 `contents`는 `["Hello", "Hi~", "질문"]` 형식의 단순 문자열 배열. LangChain 메시지 객체를 문자열로 변환해야 함
2. **systemPrompt 분리**: 시스템 메시지는 `contents`가 아닌 `systemPrompt` 필드로 별도 전달
3. **JSON 출력 안정성**: Gauss가 ReAct JSON 형식을 안정적으로 출력하지 못할 수 있음 → Few-shot 예제 필수, 파싱 실패 시 재시도 로직 구현
4. **토큰 비용**: ReAct는 각 도구 호출마다 전체 LLM 라운드트립 필요 → 불필요한 도구 호출 최소화
5. **헤더 키 확인**: `x-openapi-token`이 올바른 인증 헤더 이름입니다
6. **프록시 우회**: 사내망에서는 `proxies={'http': None, 'https': None}` 및 `verify=False` 필수 — `ChatGauss`가 기본값으로 자동 적용

## 파일 구조

```
.cline/skills/gauss-langchain-integration/
├── SKILL.md              ← 지금 읽고 있는 파일
├── docs/
│   ├── langchain-basics.md ← LangChain/LangGraph 기초 문법 (import, LCEL, Tool, Parser, Message)
│   ├── gauss-wrapper.md  ← ChatGauss(BaseChatModel) 상세 구현
│   ├── react-agent.md    ← ReAct 에이전트 구축 가이드
│   ├── langgraph-agent.md ← LangGraph StateGraph 패턴
│   ├── tools-catalog.md  ← 일반 도구 8종 구현
│   └── mcp-integration.md ← MCP 어댑터 연동
└── templates/
    ├── gauss_llm.py      ← ChatGauss 클래스 (복사해서 바로 사용)
    ├── react_agent.py    ← ReAct 에이전트 (복사해서 바로 사용)
    ├── tools.py          ← 도구 모음 (복사해서 바로 사용)
    └── .env.example       ← 환경변수 템플릿 (cp .env.example .env 후 값 입력)
```

각 docs/ 파일에 완전한 구현 코드와 설명이 포함되어 있습니다. templates/ 파일은 즉시 복사해서 사용할 수 있는 Python 코드입니다.

## 프롬프트 튜닝 가이드

Gauss의 ReAct 형식 준수 능력에 따라 프롬프트를 선택합니다. `templates/prompts.py`에 4가지 변형이 준비되어 있습니다.

| 프롬프트 | 특징 | 사용 시점 |
| --- | --- | --- |
| `STRICT_REACT_PROMPT` | 다수 Few-shot + 네거티브 가이드 + 도구 선택표 | **시작점 (권장)** |
| `KOREAN_REACT_PROMPT` | 순수 한국어, 간결 | Gauss가 한국어 지시를 잘 따를 때 |
| `MINIMAL_REACT_PROMPT` | 최소 토큰, Few-shot 1개 | 형식 준수가 확인된 후 |
| `ROBUST_REACT_PROMPT` | 틀린 예시 명시 + 올바른 예시 | 파싱 에러 20% 이상일 때 |

### 튜닝 절차

1. `STRICT_REACT_PROMPT`로 시작
2. 10-20개 다양한 질문으로 테스트
3. 파싱 실패율 측정
   - 20% 이상 → `ROBUST_REACT_PROMPT` 시도
   - 10% 미만 → `KOREAN_REACT_PROMPT` 또는 `MINIMAL_REACT_PROMPT` 시도
4. 최적 프롬프트 선정 후 `react_agent.py`의 기본 프롬프트 교체

### 핵심 튜닝 파라미터

```python
# JSON 출력 안정성을 위한 ChatGauss 설정
gauss = ChatGauss(
    temperature=0.1,           # 낮을수록 일관된 형식
    max_new_tokens=4096,       # 추론 과정 포함하므로 충분히
    repetition_penalty=1.0,    # 1.0으로 비활성화 (JSON 구조 보존)
)
```

### 파싱 실패 시 자동 재시도

```python
from prompts import PARSING_ERROR_MESSAGE

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=PARSING_ERROR_MESSAGE,  # 커스텀 에러 메시지
    max_iterations=10,
)
```