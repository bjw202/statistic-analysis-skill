# ChatGauss 래퍼 상세 가이드

## 공식 문서 참조

최신 BaseChatModel API가 필요하면: @https://docs.langchain.com/oss/python/langchain/models

## 개요

Gauss LLM을 LangChain에서 사용하려면 `BaseChatModel`을 확장한 래퍼 클래스가 필요합니다.
완성된 코드는 `templates/gauss_llm.py`에 있으며, 이 문서는 구현 상세를 설명합니다.

## 아키텍처

```
LangChain Agent/Chain
    ↓ invoke([HumanMessage, ...])
ChatGauss (BaseChatModel)
    ↓ _convert_messages() → (system_prompt, contents)
    ↓ _build_body() → API 요청 JSON
    ↓ requests.post() → Gauss REST API
    ↓ 응답 파싱 → AIMessage
LangChain Agent/Chain
```

## 메시지 변환 규칙

Gauss API의 `contents`는 **단순 문자열 리스트**입니다. LangChain의 메시지 객체를 변환해야 합니다.

| LangChain 메시지 | Gauss 매핑 |
|-----------------|-----------|
| `SystemMessage` | `systemPrompt` 필드 (별도) |
| `HumanMessage` | `contents` 리스트에 추가 |
| `AIMessage` | `contents` 리스트에 추가 |
| `ToolMessage` | `contents` 리스트에 문자열로 추가 |

### 변환 예시

```python
# LangChain 메시지
messages = [
    SystemMessage(content="당신은 도움이 되는 어시스턴트입니다."),
    HumanMessage(content="안녕하세요"),
    AIMessage(content="안녕하세요! 무엇을 도와드릴까요?"),
    HumanMessage(content="오늘 날씨 어때?"),
]

# Gauss API 변환 결과
system_prompt = "당신은 도움이 되는 어시스턴트입니다."
contents = [
    "안녕하세요",
    "안녕하세요! 무엇을 도와드릴까요?",
    "오늘 날씨 어때?",
]
```

## 핵심 구현 포인트

### 1. BaseChatModel 상속

```python
from langchain_core.language_models.chat_models import BaseChatModel

class ChatGauss(BaseChatModel):
    # 필수 구현: _generate()
    # 선택 구현: _stream() (스트리밍 지원 시)
    # 필수 프로퍼티: _llm_type
```

### 2. _generate() 메서드

`_generate()`는 BaseChatModel의 핵심 메서드로, `invoke()` 호출 시 실행됩니다.

```python
def _generate(self, messages, stop=None, run_manager=None, **kwargs):
    # 1. 메시지 변환
    system_prompt, contents = self._convert_messages(messages)

    # 2. API 요청 본문 구성
    body = {
        "modelIds": [self.model_id],
        "contents": contents,
        "llmConfig": { ... },
        "isStream": False,
    }
    if system_prompt:
        body["systemPrompt"] = system_prompt

    # 3. API 호출
    response = requests.post(api_url, headers=headers, json=body)

    # 4. 응답 파싱
    content = response.json().get("content", "")

    # 5. ChatResult 반환
    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
```

### 3. 스트리밍 지원

Gauss는 `isStream: true`로 SSE 스트리밍을 지원합니다.

```python
def _stream(self, messages, stop=None, run_manager=None, **kwargs):
    import sseclient

    body["isStream"] = True
    response = requests.post(api_url, headers=headers, json=body, stream=True)

    client = sseclient.SSEClient(response)
    for event in client.events():
        chunk_data = json.loads(event.data)
        if chunk_data.get("event_status") == "CHUNK" and chunk_data.get("content"):
            yield ChatGenerationChunk(
                message=AIMessageChunk(content=chunk_data["content"])
            )
```

## Gauss API 헤더

```python
headers = {
    "Content-Type": "application/json",
    "x-generative-ai-client": CLIENT_KEY,      # 클라이언트 키
    "x-openapi-token": PASS_KEY,               # 패스 키
    "x-generative-ai-user-email": USER_EMAIL,  # 사용자 이메일
}
```

## 프록시 설정 (사내망 필수)

Gauss 서버는 사내망에서 운영되므로 프록시 우회 설정이 필요합니다. `ChatGauss`는 기본값으로 자동 적용합니다.

```python
# 기본값: 사내망 프록시 우회 자동 적용 (별도 설정 불필요)
gauss = ChatGauss.from_env()

# 커스텀 프록시 설정이 필요한 경우
gauss = ChatGauss(
    ...,
    proxies={"http": None, "https": None},  # 프록시 비활성화 (기본값)
)
```

`_generate()`와 `_stream()` 양쪽 모두 `proxies` 및 `verify=False`가 적용됩니다.

## llmConfig 파라미터 설명

| 파라미터 | 기본값 | 설명 |
|---------|-------|------|
| `max_new_tokens` | 2024 | 생성할 최대 토큰 수 |
| `temperature` | 0.4 | 샘플링 온도 (0: 결정적, 1: 창의적) |
| `top_k` | 14 | 상위 K개 토큰에서 샘플링 |
| `top_p` | 0.94 | 누적 확률 기반 샘플링 |
| `repetition_penalty` | 1.04 | 반복 억제 (1.0: 없음) |
| `seed` | None | 재현성을 위한 시드 값 |

### ReAct 에이전트용 권장 설정

ReAct 에이전트에서는 **JSON 출력 안정성**이 중요하므로:

```python
gauss = ChatGauss(
    temperature=0.1,           # 낮은 온도로 일관된 출력
    max_new_tokens=4096,       # 충분한 토큰 (추론 과정 포함)
    repetition_penalty=1.0,    # 반복 억제 비활성화 (JSON 구조 보존)
)
```

## 에러 처리

```python
try:
    response = gauss.invoke(messages)
except requests.exceptions.ConnectionError:
    # 사내망 연결 실패
    print("Gauss 서버에 연결할 수 없습니다. VPN 연결을 확인하세요.")
except requests.exceptions.Timeout:
    # 타임아웃
    print("응답 시간 초과. max_new_tokens를 줄이거나 timeout을 늘리세요.")
except requests.exceptions.HTTPError as e:
    # API 에러 (인증 실패 등)
    print(f"API 에러: {e.response.status_code} - {e.response.text}")
```

## 테스트

```python
from gauss_llm import ChatGauss
from langchain_core.messages import HumanMessage

gauss = ChatGauss.from_env()

# 기본 호출 테스트
response = gauss.invoke([HumanMessage(content="1 + 1은?")])
print(response.content)  # "2입니다" 등

# 시스템 프롬프트 테스트
from langchain_core.messages import SystemMessage
response = gauss.invoke([
    SystemMessage(content="모든 답변을 영어로 하세요"),
    HumanMessage(content="안녕하세요"),
])
print(response.content)  # "Hello!" 등

# 스트리밍 테스트
for chunk in gauss.stream([HumanMessage(content="파이썬이란?")]):
    print(chunk.content, end="", flush=True)
```
