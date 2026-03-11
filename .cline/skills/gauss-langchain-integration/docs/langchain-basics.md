# LangChain / LangGraph 기초 문법 레퍼런스

LangChain 0.3+ / LangGraph 0.2+ 기준.

**이 스킬에서 LLM은 항상 ChatGauss입니다.** 아래 모든 예시의 `llm` 변수는 다음과 같이 초기화합니다:

```python
from gauss_llm import ChatGauss
llm = ChatGauss.from_env()  # 모든 예시에서 이 llm을 사용
```

**Gauss 제약으로 사용 불가한 패턴** (코드에 등장해도 Gauss에서는 동작하지 않음):
- `llm.bind_tools(tools)` → 사용 불가
- `ToolNode` (langgraph.prebuilt) → 사용 불가
- `create_react_agent` (langgraph.prebuilt) → 사용 불가
- 대신: `docs/react-agent.md`의 ReAct 텍스트 파싱 방식 사용

---

## 1. Import 경로 완전 정리

LangChain은 패키지가 분리되어 있습니다. 잘못된 import가 가장 많은 수정의 원인입니다.

### 패키지별 역할

| 패키지 | 역할 | pip 설치 |
| --- | --- | --- |
| `langchain_core` | 기본 추상화 (Message, Runnable, Tool 등) | `pip install langchain-core` |
| `langchain` | 고수준 체인, 에이전트 | `pip install langchain` |
| `langchain_community` | 써드파티 통합 (검색, DB 등) | `pip install langchain-community` |
| `langgraph` | 상태 그래프 기반 에이전트 | `pip install langgraph` |

### 자주 쓰는 import 모음

```python
# --- 메시지 타입 ---
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,        # 도구 실행 결과를 LLM에 피드백할 때
    BaseMessage,        # 타입 힌트용
)

# --- 프롬프트 ---
from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    MessagesPlaceholder, # 대화 기록 삽입용
)

# --- Output Parser ---
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
)
from langchain_core.pydantic_v1 import BaseModel, Field  # JsonOutputParser와 함께 사용

# --- Tool ---
from langchain_core.tools import tool, BaseTool
from langchain.tools import StructuredTool

# --- Runnable 유틸리티 ---
from langchain_core.runnables import (
    RunnablePassthrough,   # 입력을 그대로 통과
    RunnableLambda,        # 함수를 Runnable로 변환
    RunnableParallel,      # 병렬 실행
)

# --- LangGraph ---
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages  # 메시지 누적 reducer
from langgraph.prebuilt import ToolNode, create_react_agent  # 내장 패턴
from langgraph.checkpoint.memory import MemorySaver  # 인메모리 체크포인터
```

---

## 2. 메시지 타입 사용 기준

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# SystemMessage: 시스템 지시사항 (대화 맨 앞)
system = SystemMessage(content="당신은 도움이 되는 어시스턴트입니다.")

# HumanMessage: 사용자 입력
human = HumanMessage(content="안녕하세요")

# AIMessage: LLM 응답 (invoke() 반환값이 AIMessage)
ai = AIMessage(content="안녕하세요! 무엇을 도와드릴까요?")

# ToolMessage: 도구 실행 결과를 LLM에 전달할 때
# tool_call_id는 AIMessage.tool_calls[0]["id"]와 매칭되어야 함
tool_result = ToolMessage(
    content="도구 실행 결과",
    tool_call_id="call_abc123"
)

# 일반적인 대화 호출 방식
from gauss_llm import ChatGauss  # 또는 ChatOpenAI, ChatAnthropic 등 어떤 BaseChatModel이든
llm = ChatGauss.from_env()

messages = [system, human]
response = llm.invoke(messages)  # 반환값: AIMessage
print(response.content)
```

---

## 3. LCEL (LangChain Expression Language) - 파이프 문법

LCEL은 LangChain 0.2+의 핵심. `|` 연산자로 체인을 구성합니다.

### 기본 패턴

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatGauss.from_env()

# 프롬프트 | LLM | 파서 체인
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 번역가입니다."),
    ("human", "{text}를 영어로 번역해주세요."),
])

chain = prompt | llm | StrOutputParser()

# 실행
result = chain.invoke({"text": "안녕하세요"})
print(result)  # "Hello"

# 스트리밍
for chunk in chain.stream({"text": "안녕하세요"}):
    print(chunk, end="", flush=True)

# 배치 처리
results = chain.batch([{"text": "안녕"}, {"text": "반갑습니다"}])
```

### 변수 전달 패턴

```python
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# 입력을 그대로 다음 단계에 전달하면서 추가 키를 삽입
chain = (
    RunnablePassthrough.assign(word_count=lambda x: len(x["text"].split()))
    | prompt
    | llm
    | StrOutputParser()
)

# 함수를 체인에 삽입
chain = prompt | llm | RunnableLambda(lambda msg: msg.content.upper())
```

### 병렬 실행

```python
from langchain_core.runnables import RunnableParallel

chain = RunnableParallel(
    translation=translate_chain,
    summary=summarize_chain,
)
result = chain.invoke({"text": "긴 텍스트..."})
# result = {"translation": "...", "summary": "..."}
```

---

## 4. Output Parser 종류

### StrOutputParser - 문자열 추출

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": "질문"})
# result는 str
```

### JsonOutputParser - JSON 추출

```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# 스키마 정의 (선택사항, 정의하면 프롬프트에 포맷 지시가 자동 추가됨)
class Answer(BaseModel):
    answer: str = Field(description="답변 내용")
    confidence: float = Field(description="신뢰도 0.0-1.0")

parser = JsonOutputParser(pydantic_object=Answer)

prompt = ChatPromptTemplate.from_messages([
    ("system", "JSON 형식으로 답하세요.\n{format_instructions}"),
    ("human", "{question}"),
]).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser
result = chain.invoke({"question": "파이썬이란?"})
# result = {"answer": "...", "confidence": 0.9}
```

### PydanticOutputParser - Pydantic 객체 반환

```python
from langchain.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=Answer)
chain = prompt | llm | parser
result = chain.invoke({"question": "질문"})
# result는 Answer 인스턴스
print(result.answer, result.confidence)
```

---

## 5. Tool 정의 3가지 방법

### 방법 1: @tool 데코레이터 (가장 간단)

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """수학 계산을 수행합니다. 예: '2 + 3 * 4'"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"계산 에러: {e}"

@tool
def read_file(path: str) -> str:
    """파일 내용을 읽습니다."""
    with open(path) as f:
        return f.read()

# 사용
print(calculator.name)        # "calculator"
print(calculator.description) # docstring에서 자동 추출
result = calculator.invoke("2 + 3")  # "5"
```

### 방법 2: StructuredTool - 복잡한 입력

```python
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="검색어")
    max_results: int = Field(default=5, description="최대 결과 수")

def search_web(query: str, max_results: int = 5) -> str:
    """웹 검색을 수행합니다."""
    # 실제 검색 로직
    return f"{query}에 대한 검색 결과 {max_results}개"

search_tool = StructuredTool.from_function(
    func=search_web,
    name="search_web",
    description="웹에서 정보를 검색합니다.",
    args_schema=SearchInput,
)
```

### 방법 3: BaseTool 클래스 - 세밀한 제어

```python
from langchain_core.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel

class CalculatorInput(BaseModel):
    expression: str

class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = "수학 계산을 수행합니다."
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> str:
        return str(eval(expression))

    async def _arun(self, expression: str) -> str:
        return self._run(expression)  # 비동기 미지원 시 동기 호출
```

---

## 6. LangGraph 기초

### StateGraph 핵심 패턴

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 1. 상태 정의
class State(TypedDict):
    # Annotated + add_messages: 메시지를 덮어쓰지 않고 누적
    messages: Annotated[list[BaseMessage], add_messages]

# 2. 노드 함수 정의 (state 받아서 dict 반환)
# llm = ChatGauss.from_env()  ← 이 스킬에서는 항상 Gauss 사용
def my_node(state: State) -> dict:
    # state["messages"]로 현재 메시지 접근
    last_message = state["messages"][-1]
    response = llm.invoke(state["messages"])
    return {"messages": [response]}  # add_messages가 자동으로 누적

# 3. 그래프 조립
builder = StateGraph(State)
builder.add_node("my_node", my_node)
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)
graph = builder.compile()

# 4. 실행
from langchain_core.messages import HumanMessage
result = graph.invoke({"messages": [HumanMessage(content="안녕")]})
print(result["messages"][-1].content)
```

### 조건부 엣지

```python
from typing import Literal

def should_continue(state: State) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    # AIMessage에 tool_calls가 있으면 도구 실행
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "__end__"

builder.add_conditional_edges(
    "llm",           # 출발 노드
    should_continue, # 라우팅 함수
    # 명시적 매핑 (선택사항):
    # {"tools": "tool_node", "__end__": END}
)
```

### LangGraph 내장 패턴 (prebuilt) - Gauss에서 사용 불가

**아래 패턴들은 Gauss에서 동작하지 않습니다.** native tool_call을 지원하는 LLM(ChatOpenAI 등) 전용입니다.

```python
# === Gauss에서 사용 불가 ===
from langgraph.prebuilt import ToolNode, create_react_agent

tools = [calculator, read_file]
tool_node = ToolNode(tools)                    # Gauss 불가: AIMessage.tool_calls 미지원
agent = create_react_agent(llm, tools)         # Gauss 불가: bind_tools() 필요
```

**Gauss 대안**: `docs/react-agent.md`의 ReAct 텍스트 파싱 방식 또는 `docs/langgraph-agent.md`의 커스텀 그래프 사용.

### 체크포인터 (대화 기록 유지)

```python
# MemorySaver와 InMemorySaver 모두 사용 가능 (동일 기능, 이름만 다름)
from langgraph.checkpoint.memory import MemorySaver    # 구버전 이름
from langgraph.checkpoint.memory import InMemorySaver  # 신버전 이름 (최신 예시에서 주로 사용)

checkpointer = InMemorySaver()  # 또는 MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# thread_id로 대화 세션 구분
config = {"configurable": {"thread_id": "user-123"}}
result = graph.invoke({"messages": [HumanMessage(content="안녕")]}, config)

# 같은 thread_id로 이어서 호출하면 이전 대화가 자동으로 연결됨
result2 = graph.invoke({"messages": [HumanMessage(content="내가 뭐라고 했지?")]}, config)
```

---

## 7. Deprecated → 현재 API 마이그레이션

**LangChain v1부터 레거시 기능은** `langchain-classic` **패키지로 분리됨:**

```bash
pip install langchain-classic  # 레거시 코드 유지 시에만 설치
```

| 구버전 | 현재 권장 | 비고 |
| --- | --- | --- |
| `from langchain.chains import LLMChain` | `prompt | llm | parser` LCEL | 또는 `from langchain_classic.chains import LLMChain` |
| `from langchain.chains import ConversationChain` | LangGraph + `MemorySaver` | 또는 `from langchain_classic.chains import ConversationChain` |
| `ConversationBufferMemory` | `MemorySaver` / `InMemorySaver` + LangGraph | LangGraph 체크포인터로 대체 |
| `AgentExecutor` | LangGraph `StateGraph` 또는 `create_react_agent` (langgraph) | `langchain.agents` 버전은 `langchain-classic`으로 이동 |
| `initialize_agent` | `create_react_agent` (langgraph) | `langchain-classic`으로 이동 |
| `ChatOpenAI(model_name=...)` | `ChatOpenAI(model=...)` | 파라미터명 변경 |
| `from langchain.chat_models import ChatOpenAI` | `from langchain_openai import ChatOpenAI` | 패키지 분리 |
| `from langchain.tools import tool` | `from langchain_core.tools import tool` | core로 이동 |
| `from langchain.retrievers import ...` | `from langchain_classic.retrievers import ...` | langchain-classic으로 이동 |

---

## 8. Gauss를 일반 BaseChatModel처럼 쓰는 패턴

Gauss의 ChatGauss 클래스는 `BaseChatModel`을 상속합니다. 아래 패턴은 **ChatOpenAI, ChatAnthropic 등 어떤 LLM과도 동일**합니다.

```python
# 어떤 LLM이든 동일한 인터페이스
from gauss_llm import ChatGauss

llm = ChatGauss.from_env()

# 1. 직접 호출
response = llm.invoke([HumanMessage(content="안녕")])

# 2. LCEL 체인
chain = prompt | llm | StrOutputParser()

# 3. 스트리밍
for chunk in llm.stream([HumanMessage(content="파이썬이란?")]):
    print(chunk.content, end="")

# 4. 배치
responses = llm.batch([
    [HumanMessage(content="1+1은?")],
    [HumanMessage(content="2+2는?")],
])
```

### Gauss 특이사항 (일반 LLM과 다른 점)

- `bind_tools()` 미지원 → `ToolNode`, `create_react_agent` (langgraph prebuilt) 사용 불가
- 대신 `create_react_agent` (langchain.agents) + 텍스트 파싱 방식 사용
- 자세한 내용: `docs/react-agent.md` 참조