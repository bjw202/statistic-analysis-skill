# 도구 카탈로그

## 공식 문서 참조

- LangChain @tool 데코레이터: @https://docs.langchain.com/oss/python/langchain/tools
- LangChain StructuredTool: @https://docs.langchain.com/oss/python/langchain/tools#structured-tools

## 개요

Gauss ReAct 에이전트에서 사용할 수 있는 일반 도구 8종입니다.
완성된 코드는 `templates/tools.py`에 있습니다.

## 도구 목록

| 도구 | 용도 | 사내 활용 예시 |
|-----|------|-------------|
| `python_repl` | Python 코드 실행 | CSV 분석, JSON 변환, 데이터 검증 |
| `shell_exec` | 셸 명령 실행 | git log, grep, 빌드 스크립트 |
| `web_fetch` | 웹 페이지 읽기 | API 문서, 블로그, 릴리스 노트 |
| `web_search` | 정보 검색 | 최신 기술 동향, 에러 해결법 |
| `file_read` | 로컬 파일 읽기 | 설정 파일, 로그 확인 |
| `file_write` | 파일 쓰기 | 결과 저장, 코드 생성 |
| `calculator` | 수학 계산 | 성능 메트릭, 비용 계산 |
| `rest_api` | REST API 호출 | 사내 API 테스트, 헬스체크 |

## 도구 정의 방법

LangChain에서 도구를 만드는 가장 간단한 방법은 `@tool` 데코레이터입니다:

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """도구 설명 - ReAct 에이전트가 이 설명을 보고 도구를 선택합니다.

    Args:
        param: 파라미터 설명
    """
    return "결과"
```

**핵심**: docstring이 ReAct 프롬프트에 주입되므로 **명확하고 구체적으로** 작성해야 합니다.

## 각 도구 상세

### python_repl - Python 코드 실행

```python
@tool
def python_repl(code: str) -> str:
    """Python 코드를 실행하고 결과를 반환합니다."""
    result = subprocess.run(
        ["python3", "-c", code],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.strip() if result.returncode == 0 else f"에러: {result.stderr}"
```

**보안**: `exec()` 대신 `subprocess`로 격리 실행, 30초 타임아웃
**사용 예**: `python_repl("import csv; print(list(csv.reader(open('data.csv')))[:3])")`

### shell_exec - 셸 명령 실행

```python
@tool
def shell_exec(command: str) -> str:
    """셸 명령어를 실행합니다. 위험한 명령은 차단됩니다."""
    dangerous = ["rm -rf", "sudo", "mkfs", "dd if=", "> /dev/", "chmod 777"]
    # ... 위험 명령 체크 후 subprocess.run()
```

**보안**: 위험 명령 블랙리스트, 30초 타임아웃
**사용 예**: `shell_exec("git log --oneline -5")`

### web_fetch - 웹 페이지 가져오기

```python
@tool
def web_fetch(url: str) -> str:
    """URL의 웹 페이지 내용을 가져옵니다."""
    response = requests.get(url, timeout=15)
    # HTML인 경우 BeautifulSoup으로 텍스트 추출
    # 8000자 제한으로 토큰 절약
```

**의존성**: `beautifulsoup4` (선택, HTML 파싱용)
**주의**: 사내망에서는 외부 URL 접근 불가

### web_search - 웹 검색

```python
@tool
def web_search(query: str) -> str:
    """웹에서 정보를 검색합니다."""
    from duckduckgo_search import DDGS
    # DuckDuckGo 검색 (API 키 불필요)
```

**의존성**: `duckduckgo-search`
**주의**: 사내망에서 외부 검색 불가할 수 있음 → 사내 검색 API로 대체 고려

### file_read / file_write - 파일 I/O

```python
@tool
def file_read(filepath: str) -> str:
    """로컬 파일을 읽습니다."""

@tool
def file_write(filepath: str, content: str) -> str:
    """파일에 내용을 씁니다."""
```

**보안**: 프로덕션에서는 허용 디렉토리 화이트리스트 추가 권장

### calculator - 수학 계산

```python
@tool
def calculator(expression: str) -> str:
    """수학 표현식을 계산합니다."""
    allowed = set("0123456789+-*/.() ")
    # 허용된 문자만 사용 가능
```

**보안**: 숫자와 연산자만 허용하여 코드 인젝션 방지

### rest_api - REST API 호출

```python
@tool
def rest_api(method: str, url: str, body: str = None, headers: str = None) -> str:
    """REST API를 호출합니다."""
    # method, url, body(JSON문자열), headers(JSON문자열)
```

**사용 예**: `rest_api("GET", "http://internal-api.company.com/health")`

## 보안 레이어

```
Layer 1: 입력 검증 → 위험한 명령/문자 차단
Layer 2: 실행 격리 → subprocess + timeout
Layer 3: 출력 제한 → 최대 문자 수 제한 (토큰 절약)
Layer 4: 접근 제어 → 허용 경로/URL 제한 (선택)
```

### 프로덕션 보안 강화

```python
ALLOWED_DIRS = ["./data", "./output", "/tmp"]
BLOCKED_URLS = ["169.254.169.254", "localhost", "127.0.0.1"]

def validate_filepath(filepath: str) -> bool:
    import os
    abs_path = os.path.abspath(filepath)
    return any(abs_path.startswith(os.path.abspath(d)) for d in ALLOWED_DIRS)

def validate_url(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ""
    return not any(blocked in host for blocked in BLOCKED_URLS)
```

## 커스텀 도구 추가

프로젝트에 맞는 도구를 추가하려면:

```python
@tool
def jira_search(query: str) -> str:
    """사내 JIRA에서 이슈를 검색합니다.

    Args:
        query: JQL 또는 검색어
    """
    response = requests.get(
        f"https://jira.company.com/rest/api/2/search",
        params={"jql": query},
        headers={"Authorization": f"Bearer {os.environ['JIRA_TOKEN']}"},
    )
    return json.dumps(response.json()["issues"][:5], ensure_ascii=False)

# 도구 리스트에 추가
tools = get_all_tools() + [jira_search]
```

## 도구 선택 프롬프트 가이드

ReAct 프롬프트에 다음을 추가하면 Gauss의 도구 선택 정확도가 향상됩니다:

```
도구 선택 기준:
- 수학 계산이 필요하면 → calculator
- Python 코드 실행이 필요하면 → python_repl
- 셸 명령(ls, git, grep 등)이 필요하면 → shell_exec
- 웹 페이지 내용을 읽어야 하면 → web_fetch
- 정보를 검색해야 하면 → web_search
- 로컬 파일을 읽어야 하면 → file_read
- 파일을 저장해야 하면 → file_write
- HTTP API를 호출해야 하면 → rest_api

주의사항:
- 한 번에 하나의 도구만 사용하세요
- 간단한 계산은 calculator를, 복잡한 로직은 python_repl을 사용하세요
- web_fetch는 URL을 알 때, web_search는 URL을 모를 때 사용하세요
```
