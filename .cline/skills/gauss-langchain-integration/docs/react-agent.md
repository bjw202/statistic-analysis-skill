# ReAct 에이전트 구축 가이드

## 공식 문서 참조

- LangChain 도구 정의: @https://docs.langchain.com/oss/python/langchain/tools
- LangChain 에이전트 개요: @https://docs.langchain.com/oss/python/langchain/agents

## 개요

ReAct(Reasoning + Acting) 에이전트는 LLM이 **프롬프트 기반으로** 도구를 호출하는 방식입니다. Gauss처럼 네이티브 `tool_call`을 지원하지 않는 LLM에서 도구 호출을 구현하는 핵심 방법입니다.

완성된 코드는 `templates/react_agent.py`에 있습니다.

## 동작 원리

```
사용자 질문
    ↓
Gauss LLM (ReAct 프롬프트 + 도구 설명 주입)
    ↓ 텍스트 출력: "Thought: ... Action: tool_name Action Input: ..."
LangChain 파서 (텍스트에서 Action/Action Input 추출)
    ↓
도구 실행 (LangChain이 로컬에서 함수 호출)
    ↓ Observation: 도구 결과
Gauss LLM (이전 맥락 + Observation 포함)
    ↓ "Thought: ... Final Answer: ..."
최종 답변 반환
```

**핵심**: LLM이 직접 도구를 호출하는 것이 아니라, LangChain이 텍스트를 파싱하여 처리합니다.

## LangChain의 create_react_agent 사용

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

# 1. Gauss LLM 준비
from gauss_llm import ChatGauss
gauss = ChatGauss.from_env()

# 2. 도구 준비
from tools import get_all_tools
tools = get_all_tools()

# 3. ReAct 프롬프트 정의 (아래 상세 설명)
prompt = PromptTemplate.from_template(REACT_TEMPLATE)

# 4. 에이전트 생성
agent = create_react_agent(gauss, tools, prompt)

# 5. AgentExecutor로 감싸기 (실제 실행 담당)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=10,          # 최대 도구 호출 횟수
    handle_parsing_errors=True, # 파싱 실패 시 자동 재시도
    verbose=True,               # 추론 과정 출력
    early_stopping_method="generate",  # 최대 반복 도달 시 최종 답변 생성
)

# 6. 실행
result = executor.invoke({"input": "사용자 질문"})
print(result["output"])
```

## ReAct 프롬프트 설계

### 필수 변수

`create_react_agent`는 프롬프트에 다음 변수를 요구합니다:

| 변수 | 설명 |
| --- | --- |
| `{tools}` | 도구 설명 목록 (자동 주입) |
| `{tool_names}` | 도구 이름 목록 (자동 주입) |
| `{input}` | 사용자 입력 (자동 주입) |
| `{agent_scratchpad}` | 이전 추론 과정 (자동 주입) |

### Gauss 최적화 프롬프트 구조

```
1. 역할 설명 + 도구 목록
2. 응답 형식 정의 (Thought/Action/Action Input/Observation/Final Answer)
3. Few-shot 예시 (1-2개) ← Gauss의 JSON 안정성을 위해 필수
4. 도구 선택 가이드라인
5. 주의사항
6. 실제 질문 + scratchpad
```

### Few-shot 예시가 중요한 이유

Gauss는 범용 LLM이므로 ReAct 형식을 정확히 따르지 못할 수 있습니다. Few-shot 예시를 포함하면 출력 안정성이 크게 향상됩니다.

**나쁜 예** (Few-shot 없음):

```
Thought: 계산해보겠습니다
python_repl로 계산합니다: print(1+1)  ← 형식 미준수
```

**좋은 예** (Few-shot 포함 후):

```
Thought: Python으로 계산해보겠습니다.
Action: python_repl
Action Input: print(1+1)
```

## 파싱 에러 처리

### handle_parsing_errors=True

LangChain의 `AgentExecutor`에서 `handle_parsing_errors=True`를 설정하면, 파싱 실패 시 에러 메시지를 LLM에게 다시 보내 올바른 형식으로 재시도합니다.

```python
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True,
    # 또는 커스텀 에러 메시지:
    # handle_parsing_errors="올바른 형식으로 다시 작성해주세요. "
    #     "반드시 Action: 과 Action Input: 형식을 따르세요.",
)
```

### 커스텀 출력 파서

더 세밀한 제어가 필요하면 출력 파서를 커스터마이징할 수 있습니다:

```python
from langchain.agents.output_parsers import ReActSingleInputOutputParser
import re

class GaussReActOutputParser(ReActSingleInputOutputParser):
    """Gauss 출력에 최적화된 파서"""

    def parse(self, text: str):
        # Gauss가 코드블록으로 감싸는 경우 처리
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)

        # 기본 파서로 파싱 시도
        try:
            return super().parse(text)
        except Exception:
            # "Final Answer:" 패턴 직접 탐색
            if "Final Answer:" in text:
                return AgentFinish(
                    return_values={"output": text.split("Final Answer:")[-1].strip()},
                    log=text,
                )
            raise
```

## 대화 기록 유지

에이전트에 메모리를 추가하여 대화 맥락을 유지할 수 있습니다:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=False,  # ReAct는 문자열 기반
)

# 프롬프트에 {chat_history} 변수 추가 필요
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    handle_parsing_errors=True,
)
```

## 성능 최적화 팁

1. **도구 설명을 명확하게**: 도구 docstring이 정확할수록 Gauss가 올바른 도구를 선택
2. **도구 수 제한**: 10개 이하 권장. 너무 많으면 프롬프트가 길어져 성능 저하
3. **temperature 낮추기**: `temperature=0.1`로 일관된 JSON 출력 유도
4. **max_new_tokens 충분히**: ReAct 추론 과정이 길 수 있으므로 4096 이상 권장
5. **불필요한 도구 제거**: 작업에 필요한 도구만 제공하여 선택 정확도 향상

## 디버깅

```python
# verbose=True로 추론 과정 확인
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 또는 LangChain 디버그 모드
import langchain
langchain.debug = True

result = executor.invoke({"input": "테스트 질문"})
```

## 프롬프트 튜닝

`templates/prompts.py`에 4가지 프롬프트 변형이 준비되어 있습니다.

### 프롬프트 변형 사용법

```python
from prompts import STRICT_REACT_PROMPT, PARSING_ERROR_MESSAGE
from react_agent import create_gauss_agent

# STRICT 프롬프트로 에이전트 생성
agent = create_gauss_agent(
    gauss_llm=gauss,
    tools=tools,
    prompt=STRICT_REACT_PROMPT,
)

# 파싱 에러 시 커스텀 메시지로 재시도
from langchain.agents import AgentExecutor
executor = AgentExecutor(
    agent=agent.agent,  # create_gauss_agent가 반환하는 executor에서 agent 추출
    tools=tools,
    handle_parsing_errors=PARSING_ERROR_MESSAGE,
    max_iterations=10,
)
```

### 프롬프트 선택 기준

| 파싱 실패율 | 권장 프롬프트 |
| --- | --- |
| 측정 전 | `STRICT_REACT_PROMPT` (시작점) |
| 20% 이상 | `ROBUST_REACT_PROMPT` (틀린 예시 포함) |
| 10-20% | `STRICT_REACT_PROMPT` + temperature 0.05 |
| 10% 미만 | `KOREAN_REACT_PROMPT` 또는 `MINIMAL_REACT_PROMPT` |

### Gauss 모델별 튜닝 팁

**형식을 잘 따르는 모델**:

- `MINIMAL_REACT_PROMPT` 사용으로 토큰 절약
- temperature 0.2\~0.4 허용

**형식을 잘 못 따르는 모델**:

- `ROBUST_REACT_PROMPT` 사용 (틀린 예시가 효과적)
- temperature 0.05\~0.1로 매우 낮게
- `repetition_penalty=1.0` (반복 억제 비활성화)
- Few-shot 예시를 3개 이상으로 확대

**한국어에 강한 모델**:

- `KOREAN_REACT_PROMPT` 사용
- 도구 설명(docstring)도 한국어로 작성
- Action Input 예시도 한국어 포함

### 파싱 실패율 측정 스크립트

```python
"""test_parsing.py - 파싱 실패율 측정"""

test_questions = [
    "1 + 1은?",
    "현재 시간을 알려줘",
    "파이썬에서 리스트 정렬 방법은?",
    "requirements.txt 파일을 읽어줘",
    "현재 디렉토리의 파일 목록을 보여줘",
    "네이버 주가를 검색해줘",
    "피보나치 수열 10번째 값은?",
    "이 프로젝트의 README를 요약해줘",
    "2의 10승은?",
    "git log 최근 5개를 보여줘",
]

success = 0
fail = 0

for q in test_questions:
    try:
        result = executor.invoke({"input": q})
        if result.get("output"):
            success += 1
            print(f"OK: {q}")
        else:
            fail += 1
            print(f"EMPTY: {q}")
    except Exception as e:
        fail += 1
        print(f"FAIL: {q} - {e}")

total = success + fail
print(f"\n성공: {success}/{total} ({success/total*100:.0f}%)")
print(f"실패: {fail}/{total} ({fail/total*100:.0f}%)")
```

## 제한사항

- **정확도**: 네이티브 tool_call보다 낮음 (Gauss의 지시 따르기 능력에 의존)
- **속도**: 매 도구 호출마다 전체 LLM 라운드트립 필요
- **토큰 비용**: 프롬프트 + 추론 과정에 토큰 소모
- **복잡한 도구 인자**: 중첩 JSON 인자는 파싱 실패율 높음 → 단순 인자 권장