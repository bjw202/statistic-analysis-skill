# Gauss LLM + LangChain Tool Calling 타당성 조사

> 작성일: 2026-03-05 목적: 사내 LLM(Gauss)에서 LangChain을 통한 Tool Calling 및 MCP 연동 가능성 조사

---

## 1. 배경

### 1.1 현재 상황

- 사내에서 **Gauss**라는 LLM 모델을 제공 중
- 보안 문제로 **사내망에서만 접근 가능**
- Gauss는 **네이티브** `tool_call` **기능을 지원하지 않음**

### 1.2 조사 목적

LangChain이 모델의 `tool_call` 응답과 무관하게 자체적으로 함수 호출을 처리하여, 네이티브 Tool Calling을 지원하지 않는 LLM에서도 MCP(Model Context Protocol) 연동이 가능한지 검증한다.

---

## 2. LangChain의 두 가지 Tool Calling 방식

### 2.1 네이티브 Tool Calling (`create_tool_calling_agent`)

- LLM의 **내장 Function Calling API**를 사용 (예: OpenAI의 `tool_calls`)
- 모델 자체가 구조화된 JSON을 출력하여 도구를 호출
- **Gauss에서는 사용 불가** — `tool_call` API 미지원

### 2.2 ReAct 프롬프트 기반 Tool Calling (`create_react_agent`)

- **프롬프트 엔지니어링**을 통해 LLM이 도구를 "호출"하도록 유도
- LLM에게 특정 JSON 형식으로 출력하도록 프롬프트에서 지시:

```json
{
  "action": "tool_name",
  "action_input": { "param": "value" }
}
```

- **LangChain이 텍스트 출력을 파싱**하여 도구 이름과 인자를 추출 → 함수를 로컬에서 실행 → 결과를 LLM에 피드백
- **네이티브** `tool_call` **지원이 필요하지 않음** — 지시를 따르고 JSON을 출력할 수 있는 모든 LLM에서 동작

> 핵심: LLM이 직접 도구를 "호출"하는 것이 아니라, **LangChain의 에이전트 루프가 오케스트레이션을 처리**한다.

---

## 3. MCP 연동 아키텍처

### 3.1 전체 흐름

```
┌─────────────────────────────────────────────────┐
│  Gauss LLM (tool_call 미지원)                    │
│  - ReAct 프롬프트와 도구 설명을 수신              │
│  - JSON 액션 블롭이 포함된 텍스트를 출력           │
└──────────────────┬──────────────────────────────┘
                   │ LangChain이 텍스트 출력을 파싱
                   ▼
┌─────────────────────────────────────────────────┐
│  LangChain Agent Loop                            │
│  - 텍스트에서 action + action_input 추출          │
│  - 매칭되는 LangChain 도구 호출                   │
└──────────────────┬──────────────────────────────┘
                   │ langchain-mcp-adapters
                   ▼
┌─────────────────────────────────────────────────┐
│  MCP Server                                      │
│  - MCP 프로토콜을 통해 도구 호출 수신              │
│  - 결과 반환                                      │
└─────────────────────────────────────────────────┘
```

### 3.2 핵심 원리

`langchain-mcp-adapters` 라이브러리가 **MCP 도구를 LangChain 도구로 변환**한다. LangChain 도구로 변환되면, ReAct를 포함한 **어떤 에이전트 유형이든** 사용 가능하며, 이는 기반 LLM의 네이티브 Tool Calling 지원 여부와 무관하다.

---

## 4. 구현 패턴 (예시 코드)

### 4.1 기본 구조

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient

# 1. MCP 서버에 연결하고 도구 로드
async with MultiServerMCPClient(servers={
    "my_server": {
        "url": "http://localhost:8080/sse",
        "transport": "sse",
    }
}) as client:
    tools = client.get_tools()

# 2. ReAct 프롬프트 사용 (tool_calling 프롬프트가 아님)
prompt = PromptTemplate.from_template("""
다음 질문에 사용 가능한 도구를 활용하여 답변하세요.
도구 목록: {tools}
도구 이름: {tool_names}

도구를 사용할 때는 다음 JSON 형식을 사용하세요:
```

{{"action": "도구\_이름", "action_input": {{...}}}}

```

항상 다음 형식을 따르세요:

Question: 답변해야 할 질문
Thought: 무엇을 해야 할지 생각
Action:
```

$JSON_BLOB

```
Observation: 액션의 결과
... (이 Thought/Action/Observation 반복 가능)
Thought: 이제 최종 답을 알았습니다
Final Answer: 원래 질문에 대한 최종 답변

Question: {input}
{agent_scratchpad}
""")

# 3. ReAct 에이전트 생성 (네이티브 tool_call 불필요)
agent = create_react_agent(gauss_llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# 4. 실행 — LangChain이 모든 것을 처리
result = executor.invoke({"input": "사용자 질문"})
```

### 4.2 Gauss LLM을 LangChain에 연동하기

Gauss를 LangChain에서 사용하려면 `BaseLLM` 또는 `BaseChatModel`을 확장해야 한다:

```python
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

class GaussLLM(BaseChatModel):
    """사내 Gauss LLM을 위한 LangChain 래퍼"""

    model_name: str = "gauss"
    api_endpoint: str = "http://gauss-internal.company.com/api/v1/chat"

    def _generate(self, messages, stop=None, **kwargs):
        # Gauss API 호출 로직 구현
        # 응답을 LangChain 메시지 형식으로 변환
        ...

    @property
    def _llm_type(self):
        return "gauss"
```

---

## 5. 비교 분석

### 5.1 ReAct (프롬프트 기반) vs 네이티브 Tool Calling

| 항목 | ReAct (프롬프트 기반) | 네이티브 Tool Calling |
| --- | --- | --- |
| LLM 요구사항 | 텍스트 생성이 가능한 모든 LLM | `tool_call` API 지원 필수 |
| 정확도 | LLM의 지시 따르기 능력에 의존 | 높음 (구조화된 출력) |
| 속도 | 느림 (추론 과정에 토큰 소모) | 빠름 (직접 함수 호출) |
| 디버깅 | 투명함 (추론 과정 가시적) | 불투명 (추론 과정 미노출) |
| 안정성 | JSON 파싱 실패 가능성 있음 | 구조화되어 일관적 |
| 토큰 비용 | 높음 (프롬프트 + 추론) | 낮음 |
| Gauss 호환성 | **가능** | **불가능** |

### 5.2 ReAct 에이전트 유형 비교

| 에이전트 유형 | 설명 | 비고 |
| --- | --- | --- |
| `ZERO_SHOT_REACT_DESCRIPTION` | 텍스트 기반 ReAct (레거시) | v0.1.0부터 deprecated |
| `create_react_agent` | 최신 ReAct 에이전트 팩토리 | **권장** |
| `create_tool_calling_agent` | 네이티브 tool_call 사용 | Gauss에서 사용 불가 |

---

## 6. Gauss 적용 시 주요 리스크

### 6.1 JSON 출력 품질

ReAct는 LLM이 유효한 JSON을 안정적으로 출력해야 한다. Gauss가 구조화된 출력에 약하면 도구 호출이 실패할 수 있다.

**완화 방안:**

- Few-shot 예제를 프롬프트에 포함
- JSON 파싱 실패 시 재시도 로직 추가
- 출력 파서(Output Parser) 커스터마이징

### 6.2 지시 따르기(Instruction Following) 능력

LLM이 ReAct 형식(`Thought → Action → Observation`)을 엄격히 따라야 한다.

**완화 방안:**

- Gauss에 최적화된 프롬프트 템플릿 개발
- 형식 위반 시 재프롬프팅 로직 구현

### 6.3 성능

각 도구 호출마다 전체 LLM 추론 라운드트립이 필요하다.

**완화 방안:**

- 불필요한 도구 호출 최소화
- 도구 설명(description)을 명확하게 작성하여 올바른 도구 선택 유도

### 6.4 프롬프트 튜닝

ReAct 프롬프트 템플릿을 Gauss의 특성에 맞게 조정해야 할 수 있다.

**완화 방안:**

- 표준 `hwchase17/react` 프롬프트 기반으로 시작
- Gauss 응답 패턴에 맞게 점진적 조정

---

## 7. 구현 로드맵 (권장)

### Phase 1: PoC (개념 증명)

1. Gauss를 LangChain의 커스텀 LLM으로 래핑 (`BaseLLM` 또는 `BaseChatModel` 확장)
2. 1\~2개의 간단한 도구로 `create_react_agent` 테스트
3. Gauss가 ReAct JSON 형식을 안정적으로 출력하는지 검증

### Phase 2: MCP 연동

4. `langchain-mcp-adapters` 설치 및 MCP 서버 연결
5. MCP 도구를 LangChain 도구로 변환하여 ReAct 에이전트에 바인딩
6. 엔드투엔드 동작 검증

### Phase 3: 안정화

7. 프롬프트 튜닝 및 에러 핸들링 강화
8. 프로덕션 환경 배포 준비

---

## 8. 결론

| 질문 | 답변 |
| --- | --- |
| LangChain이 네이티브 tool_call 없이 Tool Calling이 가능한가? | **가능하다** (ReAct 에이전트 사용) |
| MCP 연동이 가능한가? | **가능하다** (`langchain-mcp-adapters`가 MCP 도구를 LangChain 도구로 변환) |
| Gauss에서 실현 가능한가? | **조건부 가능** (Gauss의 JSON 출력 품질 및 지시 따르기 능력에 의존) |

동료가 알려준 내용은 **기술적으로 정확**하다. LangChain의 ReAct 에이전트는 프롬프트 엔지니어링을 통해 모델의 네이티브 Tool Calling 지원 없이도 도구 호출을 수행할 수 있으며, `langchain-mcp-adapters`를 통해 MCP 서버의 도구를 LangChain 도구로 변환하면 동일한 결과를 얻을 수 있다.

---

## 참고 자료

- [Tool Calling with LangChain (공식 블로그)](https://blog.langchain.com/tool-calling-with-langchain/)
- [LangChain MCP Integration 공식 문서](https://docs.langchain.com/oss/python/langchain/mcp)
- [langchain-mcp-adapters GitHub](https://github.com/langchain-ai/langchain-mcp-adapters)
- [create_react_agent vs create_tool_calling_agent 비교](https://medium.com/@anil.goyal0057/understanding-langchain-agents-create-react-agent-vs-create-tool-calling-agent-e977a9dfe31e)
- [ReAct Agent 구현 가이드 2025](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langchain-setup-tools-agents-memory/langchain-react-agent-complete-implementation-guide-working-examples-2025)
- [LangChain MCP Adapter 가이드 (Composio)](https://composio.dev/blog/langchain-mcp-adapter-a-step-by-step-guide-to-build-mcp-agents/)
- [Custom ReAct Prompt for MLX (LangChain 문서)](https://docs.langchain.com/oss/python/integrations/chat/mlx)