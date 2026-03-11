# LangGraph StateGraph 에이전트 가이드

## 공식 문서 참조

- LangGraph 퀵스타트: @https://docs.langchain.com/oss/python/langgraph/quickstart
- LangGraph 워크플로우/에이전트: @https://docs.langchain.com/oss/python/langgraph/workflows-agents
- LangGraph GitHub: @https://github.com/langchain-ai/langgraph

## 개요

LangGraph는 LLM 애플리케이션을 **상태 그래프(StateGraph)** 로 구성하는 프레임워크입니다. ReAct 에이전트보다 세밀한 제어가 필요할 때 사용합니다.

Gauss는 `bind_tools()`를 지원하지 않으므로, **텍스트 파싱 기반 커스텀 그래프**를 구현해야 합니다.

## LangGraph vs ReAct Agent 비교

| 항목 | ReAct (create_react_agent) | LangGraph (StateGraph) |
| --- | --- | --- |
| 복잡도 | 낮음 (즉시 사용 가능) | 높음 (그래프 직접 설계) |
| 유연성 | 제한적 | 높음 (커스텀 노드/엣지) |
| 상태 관리 | 기본 (scratchpad) | 고급 (커스텀 상태) |
| 에러 제어 | AgentExecutor 기본 | 노드별 세밀 제어 |
| 분기 로직 | 불가 | 조건부 엣지로 가능 |
| 추천 시나리오 | 간단한 도구 호출 | 복잡한 워크플로우 |

## 아키텍처

```
        ┌──────────────┐
        │    START     │
        └──────┬───────┘
               ↓
        ┌──────────────┐
   ┌───→│  llm_call    │ ← Gauss에 ReAct 프롬프트 전송
   │    └──────┬───────┘
   │           ↓
   │    ┌──────────────┐
   │    │ parse_output │ ← 텍스트에서 Action/Final Answer 파싱
   │    └──────┬───────┘
   │           ↓
   │    has_action? ─── No ──→ END (Final Answer 반환)
   │           │
   │          Yes
   │           ↓
   │    ┌──────────────┐
   └────│  tool_node   │ ← 도구 실행, 결과를 메시지에 추가
        └──────────────┘
```

## 완전한 구현 코드

```python
"""langgraph_gauss_agent.py - LangGraph 기반 Gauss 에이전트"""

import json
import re
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# === 1. 상태 정의 ===

class AgentState(TypedDict):
    """에이전트 상태"""
    messages: Annotated[list[BaseMessage], add_messages]
    # 파싱된 액션 정보
    current_action: str | None       # 도구 이름
    current_action_input: str | None # 도구 입력
    iteration_count: int             # 반복 횟수


# === 2. 도구 레지스트리 ===

def build_tool_registry(tools: list) -> dict:
    """도구 리스트를 이름으로 검색 가능한 딕셔너리로 변환"""
    return {tool.name: tool for tool in tools}


def build_tool_descriptions(tools: list) -> str:
    """도구 설명을 프롬프트용 텍스트로 변환"""
    descriptions = []
    for tool in tools:
        desc = f"- {tool.name}: {tool.description}"
        descriptions.append(desc)
    return "\n".join(descriptions)


# === 3. ReAct 프롬프트 생성 ===

REACT_SYSTEM_PROMPT = """당신은 도구를 사용할 수 있는 AI 어시스턴트입니다.

사용 가능한 도구:
{tool_descriptions}

## 응답 형식

반드시 다음 형식을 정확히 따르세요:

Thought: 무엇을 해야 할지 생각합니다
Action: 도구이름
Action Input: 도구에 전달할 입력값

도구 없이 답할 수 있으면:
Thought: 이제 최종 답을 알았습니다
Final Answer: 최종 답변

## 예시

Thought: 계산이 필요합니다.
Action: calculator
Action Input: 2 + 3 * 4

## 주의
- 한 번에 하나의 도구만 사용하세요
- Action은 정확한 도구 이름이어야 합니다
- 도구 결과를 받은 후 다시 Thought부터 시작하세요"""


# === 4. 노드 함수들 ===

def create_llm_call_node(gauss_llm, tools: list):
    """LLM 호출 노드 팩토리"""

    tool_descriptions = build_tool_descriptions(tools)
    system_prompt = REACT_SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions)

    def llm_call(state: AgentState) -> dict:
        """Gauss LLM을 호출하여 응답을 생성"""
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = gauss_llm.invoke(messages)
        return {
            "messages": [response],
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    return llm_call


def parse_output(state: AgentState) -> dict:
    """LLM 출력에서 Action/Final Answer를 파싱"""
    last_message = state["messages"][-1]
    text = last_message.content

    # Final Answer 패턴 탐색
    final_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if final_match:
        return {
            "current_action": None,
            "current_action_input": None,
        }

    # Action + Action Input 패턴 탐색
    action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text, re.DOTALL)

    if action_match and input_match:
        return {
            "current_action": action_match.group(1).strip(),
            "current_action_input": input_match.group(1).strip(),
        }

    # 파싱 실패: LLM에게 재시도 요청
    return {
        "messages": [HumanMessage(
            content="올바른 형식으로 응답해주세요. "
                    "'Action: 도구이름' 과 'Action Input: 입력값' 형식, "
                    "또는 'Final Answer: 최종답변' 형식을 사용하세요."
        )],
        "current_action": "__retry__",
        "current_action_input": None,
    }


def create_tool_node(tools: list):
    """도구 실행 노드 팩토리"""

    registry = build_tool_registry(tools)

    def tool_node(state: AgentState) -> dict:
        """파싱된 액션에 따라 도구를 실행"""
        action = state["current_action"]
        action_input = state["current_action_input"]

        if action not in registry:
            observation = f"에러: '{action}' 도구를 찾을 수 없습니다. 사용 가능한 도구: {list(registry.keys())}"
        else:
            try:
                tool = registry[action]
                observation = tool.invoke(action_input)
            except Exception as e:
                observation = f"도구 실행 에러: {str(e)}"

        # Observation을 HumanMessage로 추가 (Gauss가 대화 맥락으로 인식)
        return {
            "messages": [HumanMessage(content=f"Observation: {observation}\n\nThought:")],
            "current_action": None,
            "current_action_input": None,
        }

    return tool_node


# === 5. 라우팅 함수 ===

def should_continue(state: AgentState) -> Literal["tool_node", "llm_call", "__end__"]:
    """다음 노드를 결정"""
    action = state.get("current_action")
    iteration = state.get("iteration_count", 0)

    # 최대 반복 횟수 초과
    if iteration > 10:
        return "__end__"

    # 파싱 실패 → LLM 재호출
    if action == "__retry__":
        return "llm_call"

    # 액션이 있으면 도구 실행
    if action:
        return "tool_node"

    # Final Answer → 종료
    return "__end__"


# === 6. 그래프 조립 ===

def create_gauss_langgraph_agent(gauss_llm, tools: list):
    """LangGraph 기반 Gauss 에이전트 생성

    Args:
        gauss_llm: ChatGauss 인스턴스
        tools: LangChain 도구 리스트

    Returns:
        컴파일된 LangGraph 에이전트
    """
    builder = StateGraph(AgentState)

    # 노드 추가
    builder.add_node("llm_call", create_llm_call_node(gauss_llm, tools))
    builder.add_node("parse_output", parse_output)
    builder.add_node("tool_node", create_tool_node(tools))

    # 엣지 연결
    builder.add_edge(START, "llm_call")
    builder.add_edge("llm_call", "parse_output")
    builder.add_conditional_edges("parse_output", should_continue)
    builder.add_edge("tool_node", "llm_call")

    return builder.compile()


# === 7. 사용 예시 ===

def main():
    import os
    from gauss_llm import ChatGauss
    from tools import get_all_tools

    gauss = ChatGauss(
        endpoint_url=os.environ["GAUSS_ENDPOINT"],
        client_key=os.environ["GAUSS_CLIENT_KEY"],
        pass_key=os.environ["GAUSS_PASS_KEY"],
        user_email=os.environ["GAUSS_EMAIL"],
        model_id=os.environ["GAUSS_MODEL_ID"],
        temperature=0.1,       # JSON 안정성
        max_new_tokens=4096,   # 충분한 토큰
    )

    agent = create_gauss_langgraph_agent(gauss, get_all_tools())

    # 실행
    result = agent.invoke({
        "messages": [HumanMessage(content="현재 디렉토리의 Python 파일 목록을 보여줘")],
        "current_action": None,
        "current_action_input": None,
        "iteration_count": 0,
    })

    # 마지막 AI 메시지에서 Final Answer 추출
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and "Final Answer:" in msg.content:
            answer = msg.content.split("Final Answer:")[-1].strip()
            print(f"답변: {answer}")
            break


if __name__ == "__main__":
    main()
```

## 확장 패턴

### 조건부 분기 (멀티 에이전트)

```python
# 질문 유형에 따라 다른 도구셋 사용
def route_by_topic(state: AgentState) -> Literal["code_tools", "search_tools"]:
    last_msg = state["messages"][-1].content
    if any(kw in last_msg for kw in ["코드", "파이썬", "실행"]):
        return "code_tools"
    return "search_tools"

builder.add_conditional_edges("parse_topic", route_by_topic)
```

### 상태에 커스텀 데이터 추가

```python
class ExtendedState(AgentState):
    """확장 상태"""
    search_results: list[str]      # 검색 결과 축적
    error_count: int               # 에러 카운트
    final_answer: str | None       # 최종 답변
```

### Human-in-the-Loop

```python
from langgraph.checkpoint.memory import MemorySaver

# 체크포인트로 중간 상태 저장
checkpointer = MemorySaver()
agent = builder.compile(checkpointer=checkpointer)

# 실행 후 중단점에서 사용자 입력 대기
config = {"configurable": {"thread_id": "session-1"}}
result = agent.invoke(initial_state, config)
```