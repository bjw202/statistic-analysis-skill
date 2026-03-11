"""gauss_llm.py - Gauss LLM을 LangChain에서 사용하기 위한 래퍼 클래스

사용법:
    from gauss_llm import ChatGauss

    gauss = ChatGauss(
        endpoint_url="http://gauss-internal.company.com",
        client_key="your-client-key",
        pass_key="your-pass-key",
        user_email="user@company.com",
        model_id="model-id",
    )
    response = gauss.invoke([HumanMessage(content="안녕하세요")])

환경변수로 설정 시:
    gauss = ChatGauss.from_env()

필요한 환경변수 (.env 파일 예시):
    # .env.example 참고 - 아래 변수들을 .env 파일에 설정하세요.
    #
    # GAUSS_ENDPOINT=http://gauss-internal.company.com
    # GAUSS_CLIENT_KEY=your-client-key
    # GAUSS_PASS_KEY=your-pass-key
    # GAUSS_EMAIL=user@company.com
    # GAUSS_MODEL_ID=your-model-id
"""

import json
import os
from typing import Any, Iterator, List, Optional

import requests
import urllib3
from dotenv import load_dotenv

# 사내망 환경에서 verify=False 사용 시 발생하는 SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 모듈 임포트 시 .env 파일을 자동으로 로드합니다.
# 프로젝트 루트의 .env 파일을 우선적으로 탐색합니다.
load_dotenv()
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class ChatGauss(BaseChatModel):
    """사내 Gauss LLM을 위한 LangChain ChatModel 래퍼.

    Gauss는 네이티브 tool_call을 지원하지 않으므로,
    ReAct 프롬프트 기반 도구 호출과 함께 사용해야 합니다.

    사내망 환경에서는 프록시 우회 설정이 필요합니다.
    proxies 파라미터로 프록시 설정을 제어할 수 있으며,
    기본값은 사내 Gauss 시스템에 맞게 프록시를 비활성화합니다.
    """

    endpoint_url: str
    client_key: str
    pass_key: str
    user_email: str
    model_id: str

    # llmConfig 파라미터
    temperature: float = 0.4
    max_new_tokens: int = 2024
    top_k: int = 14
    top_p: float = 0.94
    repetition_penalty: float = 1.04
    seed: Optional[int] = None

    # 요청 타임아웃 (초)
    request_timeout: int = 120

    # 프록시 설정: 사내망에서는 프록시를 비활성화해야 Gauss 서버에 접근 가능
    # None으로 설정하면 해당 프로토콜의 프록시를 우회합니다.
    proxies: Optional[dict] = None

    def model_post_init(self, __context: Any) -> None:
        """인스턴스 초기화 후 프록시 기본값을 설정합니다."""
        if self.proxies is None:
            # 사내 Gauss 시스템 기본값: HTTP/HTTPS 프록시 모두 비활성화
            object.__setattr__(self, "proxies", {"http": None, "https": None})

    @classmethod
    def from_env(cls) -> "ChatGauss":
        """환경변수에서 설정을 읽어 인스턴스를 생성합니다.

        .env 파일이 아직 로드되지 않은 경우를 대비해 명시적으로 load_dotenv()를
        한 번 더 호출합니다 (이중 보호 방식).
        """
        # 명시적 호출: 모듈 레벨 load_dotenv()가 동작하지 않는 경우를 대비합니다.
        load_dotenv()
        return cls(
            endpoint_url=os.environ["GAUSS_ENDPOINT"],
            client_key=os.environ["GAUSS_CLIENT_KEY"],
            pass_key=os.environ["GAUSS_PASS_KEY"],
            user_email=os.environ["GAUSS_EMAIL"],
            model_id=os.environ["GAUSS_MODEL_ID"],
        )

    @property
    def _llm_type(self) -> str:
        return "gauss"

    @property
    def _identifying_params(self) -> dict:
        return {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_new_tokens": self.max_new_tokens,
        }

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "x-generative-ai-client": self.client_key,
            "x-openapi-token": self.pass_key,
            "x-generative-ai-user-email": self.user_email,
        }

    def _convert_messages(self, messages: List[BaseMessage]) -> tuple[Optional[str], List[str]]:
        """LangChain 메시지를 Gauss API 형식으로 변환.

        Returns:
            (system_prompt, contents) 튜플
            - system_prompt: SystemMessage에서 추출 (없으면 None)
            - contents: 나머지 메시지의 문자열 리스트
        """
        system_prompt = None
        contents = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_prompt = msg.content
            elif isinstance(msg, HumanMessage):
                contents.append(msg.content if isinstance(msg.content, str) else str(msg.content))
            elif isinstance(msg, AIMessage):
                contents.append(msg.content if isinstance(msg.content, str) else str(msg.content))
            else:
                # ToolMessage 등 기타 메시지도 문자열로 변환
                contents.append(str(msg.content))

        return system_prompt, contents

    def _build_body(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        is_stream: bool = False,
    ) -> dict:
        system_prompt, contents = self._convert_messages(messages)

        body: dict[str, Any] = {
            "modelIds": [self.model_id],
            "contents": contents,
            "llmConfig": {
                "max_new_tokens": self.max_new_tokens,
                "seed": self.seed,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "repetition_penalty": self.repetition_penalty,
            },
            "isStream": is_stream,
        }

        if system_prompt:
            body["systemPrompt"] = system_prompt

        return body

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Gauss API를 호출하여 응답을 생성합니다."""
        body = self._build_body(messages, stop, is_stream=False)
        api_url = f"{self.endpoint_url}/openapi/chat/v1/messages"

        # 사내망 환경: 프록시 우회 및 SSL 검증 비활성화 적용
        response = requests.post(
            api_url,
            headers=self._build_headers(),
            json=body,
            timeout=self.request_timeout,
            proxies=self.proxies,
            verify=False,
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("content", "")

        # stop 시퀀스 처리
        if stop:
            for s in stop:
                if s in content:
                    content = content[: content.index(s)]

        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Gauss SSE 스트리밍 응답을 생성합니다.

        sseclient-py 패키지가 필요합니다: pip install sseclient-py
        """
        try:
            import sseclient
        except ImportError:
            raise ImportError(
                "스트리밍을 사용하려면 sseclient-py를 설치하세요: pip install sseclient-py"
            )

        body = self._build_body(messages, stop, is_stream=True)
        api_url = f"{self.endpoint_url}/openapi/chat/v1/messages"

        # 사내망 환경: 프록시 우회 및 SSL 검증 비활성화 적용
        response = requests.post(
            api_url,
            headers=self._build_headers(),
            json=body,
            timeout=self.request_timeout,
            stream=True,
            proxies=self.proxies,
            verify=False,
        )
        response.raise_for_status()

        client = sseclient.SSEClient(response)
        for event in client.events():
            try:
                chunk_data = json.loads(event.data)
            except json.JSONDecodeError:
                continue

            if chunk_data.get("event_status") == "CHUNK" and chunk_data.get("content"):
                content = chunk_data["content"]

                # stop 시퀀스 확인
                if stop:
                    for s in stop:
                        if s in content:
                            content = content[: content.index(s)]
                            chunk = ChatGenerationChunk(
                                message=AIMessageChunk(content=content)
                            )
                            if run_manager:
                                run_manager.on_llm_new_token(content)
                            yield chunk
                            return

                chunk = ChatGenerationChunk(
                    message=AIMessageChunk(content=content)
                )
                if run_manager:
                    run_manager.on_llm_new_token(content)
                yield chunk
