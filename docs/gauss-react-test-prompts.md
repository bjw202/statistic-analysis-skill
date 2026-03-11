# Gauss ReAct JSON 출력 테스트 프롬프트

> 목적: Gauss LLM이 ReAct 형식의 JSON을 안정적으로 출력하는지 검증 사용법: 아래 프롬프트를 Gauss 채팅에 그대로 붙여넣어 테스트

---

## 테스트 1: 기본 JSON 출력 능력 (가장 쉬운 단계)

```
당신은 도구를 사용할 수 있는 AI 어시스턴트입니다.

사용 가능한 도구:
- calculator: 수학 계산을 수행합니다. 입력: {"expression": "수학 표현식"}
- weather: 날씨 정보를 조회합니다. 입력: {"city": "도시명"}

도구를 사용할 때는 반드시 아래 JSON 형식으로만 응답하세요:

{"action": "도구이름", "action_input": {"파라미터": "값"}}

다른 텍스트 없이 JSON만 출력하세요.

질문: 서울의 날씨를 알려줘
```

**기대 응답:**

```json
{"action": "weather", "action_input": {"city": "서울"}}
```

---

## 테스트 2: ReAct 형식 (Thought + Action)

```
당신은 도구를 사용하여 질문에 답변하는 AI 어시스턴트입니다.

사용 가능한 도구:
- search: 정보를 검색합니다. 입력: {"query": "검색어"}
- calculator: 수학 계산을 수행합니다. 입력: {"expression": "수학 표현식"}

반드시 아래 형식을 따르세요:

Thought: 어떤 도구를 사용해야 할지 생각합니다
Action:
```json
{"action": "도구이름", "action_input": {"파라미터": "값"}}
```

질문: 대한민국의 인구수를 검색해줘

```

**기대 응답:**
```

Thought: 대한민국의 인구수를 알아내기 위해 search 도구를 사용해야겠습니다. Action:

```json
{"action": "search", "action_input": {"query": "대한민국 인구수"}}
```

```

---

## 테스트 3: 전체 ReAct 루프 시뮬레이션
```

당신은 도구를 사용하여 질문에 답변하는 AI 어시스턴트입니다. 반드시 아래 형식만 사용하세요. 다른 형식은 허용되지 않습니다.

사용 가능한 도구:

- search: 정보를 검색합니다. 입력: {"query": "검색어"}
- calculator: 수학 계산을 수행합니다. 입력: {"expression": "수학 표현식"}

형식 규칙:

1. 도구를 사용해야 할 때: Thought: \[생각\] Action:

```json
{"action": "도구이름", "action_input": {"파라미터": "값"}}
```

2. 최종 답변을 알 때: Thought: 이제 최종 답변을 알았습니다. Final Answer: \[답변\]

아래는 예시입니다:

Question: 7 곱하기 8은? Thought: 계산기 도구를 사용하여 7 \* 8을 계산해야겠습니다. Action:

```json
{"action": "calculator", "action_input": {"expression": "7 * 8"}}
```

Observation: 56 Thought: 이제 최종 답변을 알았습니다. Final Answer: 7 곱하기 8은 56입니다.

이제 시작하세요.

Question: 15 나누기 3 더하기 20은 얼마인가요?

```

**기대 응답:**
```

Thought: 15 나누기 3 더하기 20을 계산해야 합니다. calculator 도구를 사용하겠습니다. Action:

```json
{"action": "calculator", "action_input": {"expression": "15 / 3 + 20"}}
```

```

---

## 테스트 4: 도구 선택 능력 (여러 도구 중 올바른 것 선택)
```

당신은 도구를 사용하여 질문에 답변하는 AI 어시스턴트입니다.

사용 가능한 도구:

- get_stock_price: 주식 가격을 조회합니다. 입력: {"ticker": "종목코드"}
- search: 일반 정보를 검색합니다. 입력: {"query": "검색어"}
- calculator: 수학 계산을 수행합니다. 입력: {"expression": "수학 표현식"}
- translate: 텍스트를 번역합니다. 입력: {"text": "원문", "target_lang": "목표언어"}

도구를 사용할 때는 반드시 아래 형식으로 응답하세요:

Thought: \[어떤 도구를 왜 사용해야 하는지 설명\] Action:

```json
{"action": "도구이름", "action_input": {"파라미터": "값"}}
```

Question: "Hello, how are you?"를 한국어로 번역해줘

```

**기대 응답:**
```

Thought: 영어 텍스트를 한국어로 번역해야 하므로 translate 도구를 사용하겠습니다. Action:

```json
{"action": "translate", "action_input": {"text": "Hello, how are you?", "target_lang": "ko"}}
```

```

---

## 테스트 5: 다단계 추론 (가장 어려운 단계)
```

당신은 도구를 사용하여 복잡한 질문에 답변하는 AI 어시스턴트입니다. 한 번에 하나의 도구만 사용할 수 있습니다.

사용 가능한 도구:

- search: 정보를 검색합니다. 입력: {"query": "검색어"}
- calculator: 수학 계산을 수행합니다. 입력: {"expression": "수학 표현식"}

형식: Thought: \[생각\] Action:

```json
{"action": "도구이름", "action_input": {"파라미터": "값"}}
```

Observation 결과가 주어지면 다음 단계를 진행하세요. 최종 답을 알면 "Final Answer:"로 응답하세요.

Question: 한국의 인구가 약 5200만명이고, 일본의 인구가 약 1억 2500만명이라고 할 때, 두 나라 인구의 합은? Thought: 두 나라의 인구 합을 계산해야 합니다. 5200만 + 12500만을 계산기로 계산하겠습니다. Action:

```json
{"action": "calculator", "action_input": {"expression": "52000000 + 125000000"}}
```

Observation: 177000000

```

**기대 응답:**
```

Thought: 이제 최종 답변을 알았습니다. 두 나라 인구의 합은 1억 7700만명입니다. Final Answer: 한국(약 5200만명)과 일본(약 1억 2500만명)의 인구 합은 약 1억 7700만명(177,000,000명)입니다.

```

---

## 평가 기준

| 테스트 | 통과 조건 | 중요도 |
| --- | --- | --- |
| 테스트 1 | 유효한 JSON 출력, 올바른 도구 선택 | 필수 |
| 테스트 2 | Thought + Action 형식 준수, 유효한 JSON | 필수 |
| 테스트 3 | 전체 ReAct 형식 준수, 예시와 유사한 구조 | 필수 |
| 테스트 4 | 4개 도구 중 올바른 도구 선택 | 중요 |
| 테스트 5 | Observation 후 Final Answer 생성 | 권장 |

### 판정 기준

- **테스트 1~3 모두 통과**: ReAct 에이전트 연동 **가능** → Phase 1 PoC 진행
- **테스트 1~2만 통과**: 프롬프트 튜닝 필요, **조건부 가능** → 프롬프트 최적화 후 재시도
- **테스트 1도 실패**: ReAct 방식 **어려움** → 대안 검토 필요
```