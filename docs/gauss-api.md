# Gauss Chat API

## 

### GET /openapi/chat/v1/models

- API로 사용할 수 있는 대화 모델의 리스트를 조회합니다.
- Header 필드에는 Content-Type, x-generative-ai-client, x-openapi-token, x-generative-ai-user-email 등의 string 데이터 포함.
- Response 필드에는 modelid(String), name(list), description(list)

### POST /openapi/chat/v1/messages

- message API는 대화에 대한 모델 응답을 생성합니다.

- Header 필드에는 Content-Type, x-generative-ai-client, x-openapi-token, x-generative-ai-user-email 등의 string 데이터 포함.

- Request 필드에는 modelids(array), contents(list\[string\]), isStream(boolean), llmConfig(object), systemPrompt(string) 포함

  : llmConfig의 프로퍼티는 temerature, repetition_penalty, decoder_input_details, seed, tok_k, top_p, max_new_tokens 포함

- Response 필드에는 userID(integer), modelType(string), content(string, answer 출력), status\*string), responseCode(string) 등

## 예제 코드 (isStream=False)

```python
import requests

YOUR_CLIENT_KEY="..."
YOUR_PASS_KEY="..."
ENDPOINT_URL="..."
YOUR_MODEL_ID="Get model id from Model API"
YOUR_EMAIL=""

headers = {
"x-generative-ai-client”: YOUR_CLIENT_KEY,
“x-openapi-koten”: YOUR_PASS_KEY,
“x-generative-ai-user-email”: YOUR_EMAIL
}

body = {
“modelIds”: [YOUR_MODEL_ID],
“contents”: [“Hello”, “Hi~”, “My name is Kim”],
“llmConfig”:{
  “max_new_tokens”:2024,
  “seed”:None,
  “top_k”:14,
  “top_p”:0.94,
  “temperature”:0.4,
  repetition_penalty: 1.04
  },
“isStream”: False,
“systemPrompt”:”Hi, Answer for your client"
}

api_endpoint_url = f”{ENDPOINT_URL}/openapi/chat/v1/messages"

response=requests.post(api_endpoint_url, headers-headers, json=body)

print(response.json())
```

## 예제 코드 (isStream=True)

```python
import requests

YOUR_CLIENT_KEY="..."
YOUR_PASS_KEY="..."
ENDPOINT_URL="..."
YOUR_MODEL_ID="Get model id from Model API"
YOUR_EMAIL=""

headers = {
"x-generative-ai-client”: YOUR_CLIENT_KEY,
“x-openapi-koten”: YOUR_PASS_KEY,
“x-generative-ai-user-email”: YOUR_EMAIL
}

body = {
“modelIds”: [YOUR_MODEL_ID],
“contents”: [“Hello”, “Hi~”, “My name is Kim”],
“llmConfig”:{
  “max_new_tokens”:2024,
  “seed”:None,
  “top_k”:14,
  “top_p”:0.94,
  “temperature”:0.4,
  repetition_penalty: 1.04
  },
“isStream”: False,
“systemPrompt”:”Hi, Answer for your client"
}

api_endpoint_url = f”{ENDPOINT_URL}/openapi/chat/v1/messages"

response=requests.post(api_endpoint_url, headers-headers, json=body)

client = sseclient.SSEClient(response)

def get_result():
   for event in client.events():
      print(f”Data:{event.data}")
      yield event.data

result_message=“"
for ch in get_result():
   ch_json = json.loads(ch)
   if ch_json]'event_status'] == “CHUNK” and ch_json['content']:
      result_message += ch_json['content']

print(result_message)
```