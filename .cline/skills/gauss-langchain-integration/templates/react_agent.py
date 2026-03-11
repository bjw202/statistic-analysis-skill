"""react_agent.py - Gauss + ReAct 에이전트 조립

사용법:
    from react_agent import create_gauss_agent

    agent = create_gauss_agent(gauss_llm, tools)
    result = agent.invoke({"input": "사용자 질문"})
    print(result["output"])
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

# Gauss에 최적화된 ReAct 프롬프트 템플릿
# Few-shot 예제를 포함하여 JSON 출력 안정성을 높임
GAUSS_REACT_PROMPT = PromptTemplate.from_template(
    """다음 질문에 사용 가능한 도구를 활용하여 최선의 답변을 하세요.

사용 가능한 도구:
{tools}

도구 이름 목록: {tool_names}

## 응답 형식

반드시 다음 형식을 정확히 따르세요:

Question: 답변해야 할 질문
Thought: 무엇을 해야 할지 생각합니다
Action: 사용할 도구 이름 (도구 이름 목록 중 하나여야 합니다)
Action Input: 도구에 전달할 입력값
Observation: 도구 실행 결과 (이 줄은 시스템이 자동으로 채웁니다)
... (Thought/Action/Action Input/Observation을 필요한 만큼 반복)
Thought: 이제 최종 답을 알았습니다
Final Answer: 원래 질문에 대한 최종 답변

## 예시

Question: Python에서 1부터 10까지의 합을 구해줘
Thought: Python 코드를 실행해서 1부터 10까지의 합을 구해야 합니다. python_repl 도구를 사용하겠습니다.
Action: python_repl
Action Input: print(sum(range(1, 11)))
Observation: 55
Thought: 이제 최종 답을 알았습니다
Final Answer: 1부터 10까지의 합은 55입니다.

## 도구 선택 기준

- 수학 계산이 필요하면 → calculator
- Python 코드 실행이 필요하면 → python_repl
- 셸 명령(ls, git, grep 등)이 필요하면 → shell_exec
- 웹 페이지 내용을 읽어야 하면 → web_fetch
- 정보를 검색해야 하면 → web_search
- 로컬 파일을 읽어야 하면 → file_read
- 파일을 저장해야 하면 → file_write
- HTTP API를 호출해야 하면 → rest_api

## 주의사항

- 한 번에 하나의 도구만 사용하세요
- Action은 반드시 도구 이름 목록에 있는 이름이어야 합니다
- Action Input은 도구가 요구하는 형식의 값이어야 합니다
- 도구 없이 답변할 수 있으면 바로 Final Answer를 작성하세요

자, 시작하겠습니다!

Question: {input}
{agent_scratchpad}"""
)


def create_gauss_agent(
    gauss_llm,
    tools: list,
    prompt: PromptTemplate = GAUSS_REACT_PROMPT,
    max_iterations: int = 10,
    handle_parsing_errors: bool = True,
    verbose: bool = True,
) -> AgentExecutor:
    """Gauss LLM과 도구를 사용하는 ReAct 에이전트를 생성합니다.

    Args:
        gauss_llm: ChatGauss 인스턴스
        tools: LangChain 도구 리스트
        prompt: ReAct 프롬프트 템플릿
        max_iterations: 최대 도구 호출 반복 횟수
        handle_parsing_errors: 파싱 에러 자동 처리 여부
        verbose: 추론 과정 출력 여부

    Returns:
        AgentExecutor 인스턴스
    """
    agent = create_react_agent(gauss_llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=max_iterations,
        handle_parsing_errors=handle_parsing_errors,
        verbose=verbose,
        # 파싱 실패 시 LLM에게 다시 시도하도록 요청
        early_stopping_method="generate",
    )


# === 실행 예시 ===
if __name__ == "__main__":
    import os

    from gauss_llm import ChatGauss
    from tools import get_all_tools

    gauss = ChatGauss(
        endpoint_url=os.environ["GAUSS_ENDPOINT"],
        client_key=os.environ["GAUSS_CLIENT_KEY"],
        pass_key=os.environ["GAUSS_PASS_KEY"],
        user_email=os.environ["GAUSS_EMAIL"],
        model_id=os.environ["GAUSS_MODEL_ID"],
    )

    agent = create_gauss_agent(gauss, get_all_tools())

    # 대화형 루프
    while True:
        question = input("\n질문: ")
        if question.lower() in ("exit", "quit", "q"):
            break
        result = agent.invoke({"input": question})
        print(f"\n답변: {result['output']}")
