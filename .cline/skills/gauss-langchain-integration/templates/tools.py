"""tools.py - Gauss ReAct 에이전트용 일반 도구 모음

사용법:
    from tools import get_all_tools
    tools = get_all_tools()
"""

import json
import subprocess
from typing import Optional

import requests
from langchain_core.tools import tool


@tool
def python_repl(code: str) -> str:
    """Python 코드를 실행하고 결과를 반환합니다.
    데이터 처리, 계산, 파일 변환 등에 사용하세요.

    Args:
        code: 실행할 Python 코드
    """
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip() or "(실행 완료, 출력 없음)"
        else:
            return f"에러: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "에러: 실행 시간 초과 (30초)"
    except Exception as e:
        return f"에러: {str(e)}"


@tool
def shell_exec(command: str) -> str:
    """셸 명령어를 실행하고 결과를 반환합니다.
    파일 목록 확인, git 명령, 빌드 실행 등에 사용하세요.
    위험한 명령(rm -rf, sudo 등)은 차단됩니다.

    Args:
        command: 실행할 셸 명령어
    """
    dangerous = ["rm -rf", "sudo", "mkfs", "dd if=", "> /dev/", "chmod 777"]
    for d in dangerous:
        if d in command:
            return f"차단됨: 위험한 명령어 '{d}'는 실행할 수 없습니다."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            output += f"\n(종료 코드: {result.returncode})\n{result.stderr.strip()}"
        return output or "(실행 완료, 출력 없음)"
    except subprocess.TimeoutExpired:
        return "에러: 실행 시간 초과 (30초)"
    except Exception as e:
        return f"에러: {str(e)}"


@tool
def web_fetch(url: str) -> str:
    """URL의 웹 페이지 내용을 가져옵니다.
    API 문서, 블로그 글, 공식 문서 등의 내용을 읽을 때 사용하세요.

    Args:
        url: 가져올 웹 페이지 URL
    """
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "GaussBridge/1.0"},
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
            except ImportError:
                text = response.text
        else:
            text = response.text

        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n...(이하 생략, 총 {len(text)}자)"
        return text
    except requests.exceptions.Timeout:
        return "에러: 요청 시간 초과 (15초)"
    except requests.exceptions.RequestException as e:
        return f"에러: {str(e)}"


@tool
def web_search(query: str) -> str:
    """웹에서 정보를 검색합니다.
    최신 뉴스, 기술 정보, 문서를 찾을 때 사용하세요.

    Args:
        query: 검색어
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "검색 결과 없음"
            output = []
            for r in results:
                output.append(f"제목: {r['title']}\nURL: {r['href']}\n요약: {r['body']}\n")
            return "\n---\n".join(output)
    except ImportError:
        return "에러: duckduckgo-search 패키지 필요. pip install duckduckgo-search"
    except Exception as e:
        return f"에러: {str(e)}"


@tool
def file_read(filepath: str) -> str:
    """로컬 파일의 내용을 읽어서 반환합니다.

    Args:
        filepath: 읽을 파일의 경로
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        max_chars = 8000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n...(이하 생략, 총 {len(content)}자)"
        return content
    except FileNotFoundError:
        return f"에러: 파일을 찾을 수 없습니다 - {filepath}"
    except Exception as e:
        return f"에러: {str(e)}"


@tool
def file_write(filepath: str, content: str) -> str:
    """파일에 내용을 씁니다. 이미 존재하면 덮어씁니다.

    Args:
        filepath: 쓸 파일의 경로
        content: 파일에 쓸 내용
    """
    try:
        import os

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"파일 저장 완료: {filepath} ({len(content)}자)"
    except Exception as e:
        return f"에러: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """수학 표현식을 계산합니다.

    Args:
        expression: 계산할 수학 표현식 (예: "2 + 3 * 4")
    """
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "에러: 허용되지 않는 문자가 포함되어 있습니다."
        result = eval(expression)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"에러: {str(e)}"


@tool
def rest_api(
    method: str,
    url: str,
    body: Optional[str] = None,
    headers: Optional[str] = None,
) -> str:
    """REST API를 호출하고 응답을 반환합니다.

    Args:
        method: HTTP 메서드 (GET, POST, PUT, DELETE)
        url: API URL
        body: JSON 형식의 요청 본문 (POST/PUT 시)
        headers: JSON 형식의 추가 헤더
    """
    try:
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(json.loads(headers))
        req_body = json.loads(body) if body else None
        response = requests.request(
            method=method.upper(),
            url=url,
            json=req_body,
            headers=req_headers,
            timeout=15,
        )
        result = {
            "status_code": response.status_code,
            "body": response.text[:4000],
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"에러: {str(e)}"


def get_all_tools() -> list:
    """모든 도구를 리스트로 반환합니다."""
    return [
        python_repl,
        shell_exec,
        web_fetch,
        web_search,
        file_read,
        file_write,
        calculator,
        rest_api,
    ]
