# 도구 통합 가이드 (MCP 어댑터 + 일반 도구 조합)

> 이 문서는 Gauss 에이전트에 **여러 종류의 도구를 통합**하는 방법을 다룹니다. MCP 서버 도구 + 일반 도구(@tool)를 하나의 에이전트에서 함께 사용하는 패턴이 핵심입니다. MCP 없이 일반 도구만 사용하는 경우: `docs/react-agent.md` 참조

## 공식 문서 참조

- LangChain MCP 통합: @https://docs.langchain.com/oss/python/langchain/mcp
- langchain-mcp-adapters GitHub: @https://github.com/langchain-ai/langchain-mcp-adapters
- MCP 프로토콜 스펙: @https://modelcontextprotocol.io/introduction

## 개요

`langchain-mcp-adapters`는 MCP(Model Context Protocol) 서버의 도구를 LangChain 도구로 변환하는 라이브러리입니다. 이를 통해 MCP 도구를 ReAct 에이전트에서 일반 도구와 동일하게 사용할 수 있습니다.

## 사내 제약사항

- MCP 서버는 **사내망에서만 접근 가능**
- 외부 MCP 서버 연결 불가
- Cline에서 MCP 서버를 직접 사용할 수 없음 (코드에서 프로그래밍 방식으로만 가능)

## 설치

```bash
pip install langchain-mcp-adapters
```

## 핵심 원리

```
MCP Server (도구 제공)
    ↓ MCP 프로토콜
langchain-mcp-adapters (MultiServerMCPClient)
    ↓ MCP 도구 → LangChain 도구 변환
LangChain Agent (ReAct 등)
    ↓ 일반 도구와 동일하게 사용
Gauss LLM
```

**핵심**: MCP 도구가 LangChain 도구로 변환되면, Gauss ReAct 에이전트에서 **기존 도구와 동일한 방식**으로 사용 가능합니다.

## 기본 사용법

### stdio 트랜스포트 (로컬 프로세스)

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    async with MultiServerMCPClient(servers={
        "my_server": {
            "command": "python",
            "args": ["path/to/mcp_server.py"],
            "transport": "stdio",
        }
    }) as client:
        tools = client.get_tools()
        print(f"로드된 MCP 도구: {[t.name for t in tools]}")

asyncio.run(main())
```

### SSE 트랜스포트 (HTTP 서버)

```python
async with MultiServerMCPClient(servers={
    "my_server": {
        "url": "http://internal-mcp-server.company.com:8080/sse",
        "transport": "sse",
    }
}) as client:
    tools = client.get_tools()
```

### HTTP 스트리밍 트랜스포트

```python
async with MultiServerMCPClient(servers={
    "my_server": {
        "url": "http://internal-mcp-server.company.com:8080/mcp",
        "transport": "http",
    }
}) as client:
    tools = client.get_tools()
```

## 일반 도구 + MCP 도구 통합 에이전트

```python
"""unified_agent.py - 일반 도구 + MCP 도구를 모두 사용하는 통합 에이전트"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from gauss_llm import ChatGauss
from react_agent import create_gauss_agent
from tools import get_all_tools


async def create_unified_agent(gauss_config: dict, mcp_servers: dict):
    """일반 도구 + MCP 도구를 갖춘 통합 에이전트 생성

    Args:
        gauss_config: ChatGauss 설정
        mcp_servers: MCP 서버 설정 딕셔너리

    Returns:
        (agent, client) 튜플 - client는 컨텍스트 매니저로 관리 필요
    """
    gauss = ChatGauss(**gauss_config)

    # 일반 도구
    general_tools = get_all_tools()

    # MCP 도구
    client = MultiServerMCPClient(servers=mcp_servers)
    await client.__aenter__()
    mcp_tools = client.get_tools()

    # 모든 도구 합치기
    all_tools = general_tools + mcp_tools
    print(f"총 {len(all_tools)}개 도구 로드됨:")
    print(f"  일반 도구: {[t.name for t in general_tools]}")
    print(f"  MCP 도구: {[t.name for t in mcp_tools]}")

    agent = create_gauss_agent(gauss, all_tools)
    return agent, client


# === 사용 예시 ===

async def main():
    import os

    gauss_config = {
        "endpoint_url": os.environ["GAUSS_ENDPOINT"],
        "client_key": os.environ["GAUSS_CLIENT_KEY"],
        "pass_key": os.environ["GAUSS_PASS_KEY"],
        "user_email": os.environ["GAUSS_EMAIL"],
        "model_id": os.environ["GAUSS_MODEL_ID"],
    }

    mcp_servers = {
        # 사내 MCP 서버 예시
        "internal_docs": {
            "url": "http://mcp-docs.company.com:8080/sse",
            "transport": "sse",
        },
        # 로컬 MCP 서버 예시
        "local_db": {
            "command": "python",
            "args": ["mcp_servers/db_server.py"],
            "transport": "stdio",
        },
    }

    agent, client = await create_unified_agent(gauss_config, mcp_servers)

    try:
        # 에이전트 사용
        result = agent.invoke({
            "input": "사내 문서에서 배포 절차를 찾아서 요약해줘"
        })
        print(f"\n답변: {result['output']}")
    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())
```

## 다중 MCP 서버 연결

```python
mcp_servers = {
    # Context7 (라이브러리 문서 검색) - 사내망 접근 가능한 경우
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp@latest"],
        "transport": "stdio",
    },

    # 사내 DB 조회 서버
    "company_db": {
        "url": "http://mcp-db.company.com:3000/sse",
        "transport": "sse",
    },

    # 사내 검색 서버
    "company_search": {
        "url": "http://mcp-search.company.com:3000/sse",
        "transport": "sse",
    },
}
```

## 주의사항

1. **비동기 컨텍스트**: `MultiServerMCPClient`는 `async with`로 사용해야 합니다
2. **사내망 제한**: 외부 MCP 서버(예: 공개 Context7)는 접근 불가할 수 있습니다
3. **도구 이름 충돌**: 일반 도구와 MCP 도구의 이름이 겹치지 않도록 주의
4. **타임아웃**: MCP 서버 응답이 느리면 에이전트 전체가 지연됩니다

## MCP 서버 직접 만들기

사내용 MCP 서버를 만들어 Gauss 에이전트에 연결할 수 있습니다:

```python
"""간단한 MCP 서버 예시"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("company-tools")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_wiki",
            description="사내 위키를 검색합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어"}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_wiki":
        # 사내 위키 검색 로직
        results = search_company_wiki(arguments["query"])
        return [TextContent(type="text", text=results)]

async def main():
    async with stdio_server() as streams:
        await server.run(*streams)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

이렇게 만든 MCP 서버를 `MultiServerMCPClient`의 stdio 트랜스포트로 연결하면, Gauss ReAct 에이전트에서 사내 위키 검색 도구를 자동으로 사용할 수 있습니다.