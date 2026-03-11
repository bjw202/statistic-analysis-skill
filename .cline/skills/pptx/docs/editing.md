# 프레젠테이션 편집 가이드

기존 프레젠테이션을 템플릿으로 사용하거나 편집할 때의 워크플로우.

> 스크립트 경로: `.cline/skills/pptx/scripts/`

---

## 템플릿 기반 워크플로우

### Step 1: 기존 슬라이드 분석

```bash
python .cline/skills/pptx/scripts/thumbnail.py template.pptx
python -m markitdown template.pptx
```

- `thumbnails.jpg`로 레이아웃 파악
- markitdown 출력으로 자리표시자 텍스트 파악

### Step 2: 슬라이드 매핑 계획

각 콘텐츠 섹션에 어떤 템플릿 슬라이드를 사용할지 결정.

**단조로운 레이아웃 반복 금지.** 다음 레이아웃을 적극 활용:
- 2단 컬럼 (텍스트 + 이미지)
- 이미지 + 텍스트 조합
- 전체 블리드 이미지 + 텍스트 오버레이
- 인용/콜아웃 슬라이드
- 섹션 구분자
- 수치 콜아웃 (stat callout)
- 아이콘 그리드 또는 아이콘 + 텍스트 행

콘텐츠 유형 → 레이아웃 매칭: 핵심 포인트→불릿 슬라이드, 팀 소개→멀티컬럼, 인용→인용 슬라이드.

### Step 3: 압축 해제

```bash
python .cline/skills/pptx/scripts/office/unpack.py template.pptx unpacked/
```

### Step 4: 구조 편집 (Cline이 직접 수행)

**이 단계는 서브에이전트 없이 직접 수행해야 함.**

- 불필요한 슬라이드 삭제: `ppt/presentation.xml`의 `<p:sldIdLst>`에서 제거
- 슬라이드 복제: `add_slide.py` 사용
- 슬라이드 순서 변경: `<p:sldId>` 요소 재배열

**Step 5 전에 모든 구조 변경을 완료할 것.**

### Step 5: 내용 편집

각 `slide{N}.xml`의 텍스트 업데이트.

슬라이드는 개별 XML 파일이므로 여러 슬라이드를 병렬로 편집 가능.

각 슬라이드에서:
1. 슬라이드 XML 읽기
2. 모든 자리표시자 콘텐츠 파악 (텍스트, 이미지, 차트, 아이콘, 캡션)
3. 각 자리표시자를 최종 내용으로 교체

**`sed`나 Python 스크립트 대신 Edit 도구 사용.** Edit 도구는 무엇을 어디서 교체할지 명확하게 하여 신뢰성이 높음.

### Step 6: 정리

```bash
python .cline/skills/pptx/scripts/clean.py unpacked/
```

### Step 7: 재패킹

```bash
python .cline/skills/pptx/scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

---

## 스크립트 상세

### unpack.py

```bash
python .cline/skills/pptx/scripts/office/unpack.py input.pptx unpacked/
```

PPTX 추출, XML 포맷, 스마트 따옴표 이스케이프.

### add_slide.py

```bash
python .cline/skills/pptx/scripts/add_slide.py unpacked/ slide2.xml        # 슬라이드 복제
python .cline/skills/pptx/scripts/add_slide.py unpacked/ slideLayout2.xml  # 레이아웃에서 생성
```

`<p:sldId>` 출력 → 원하는 위치의 `<p:sldIdLst>`에 추가.

### clean.py

```bash
python .cline/skills/pptx/scripts/clean.py unpacked/
```

`<p:sldIdLst>`에 없는 슬라이드, 참조되지 않는 미디어, 고아 rels 제거.

### pack.py

```bash
python .cline/skills/pptx/scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```

검증, 수정, XML 압축, 스마트 따옴표 재인코딩.

### thumbnail.py

```bash
python .cline/skills/pptx/scripts/thumbnail.py input.pptx [output_prefix] [--cols N]
```

슬라이드 파일명을 라벨로 표시한 `thumbnails.jpg` 생성. 기본 3열, 그리드당 최대 12개.

**템플릿 분석용으로만 사용** (레이아웃 선택). 시각 QA에는 `soffice` + `pdftoppm`으로 고해상도 개별 이미지 생성 권장.

---

## 슬라이드 조작

슬라이드 순서는 `ppt/presentation.xml` → `<p:sldIdLst>`.

**순서 변경**: `<p:sldId>` 요소 재배열.

**삭제**: `<p:sldId>` 제거 후 `clean.py` 실행.

**추가**: `add_slide.py` 사용. 슬라이드 파일을 수동으로 복사하지 말 것 — 스크립트가 노트 참조, Content_Types.xml, 관계 ID를 자동 처리.

---

## 서식 규칙

- **헤더, 서브헤딩, 인라인 라벨 모두 굵게**: `<a:rPr>`에 `b="1"` 사용. 슬라이드 제목, 섹션 헤더, "상태:", "설명:" 같은 인라인 라벨 포함.
- **유니코드 불릿(•) 금지**: `<a:buChar>` 또는 `<a:buAutoNum>` 사용.
- **불릿 일관성**: 레이아웃에서 상속. `<a:buChar>` 또는 `<a:buNone>`만 지정.

---

## 자주 발생하는 문제

### 템플릿 적용

소스 내용이 템플릿보다 항목 수가 적을 때:
- **텍스트만 지우지 말고 요소 전체 제거** (이미지, 도형, 텍스트 박스)
- 텍스트 지운 후 고아 비주얼 확인
- 시각 QA로 불일치 개수 확인

다른 길이의 텍스트로 교체할 때:
- **짧은 교체**: 보통 안전
- **긴 교체**: 넘침 또는 예상치 못한 줄바꿈 가능성
- 텍스트 변경 후 시각 QA 필수

**템플릿 슬롯 ≠ 소스 항목**: 템플릿에 팀원 4명인데 소스에 3명이면, 4번째 팀원의 그룹 전체(이미지 + 텍스트 박스) 삭제.

### 다중 항목 콘텐츠

여러 항목은 반드시 별개의 `<a:p>` 요소로 — **하나의 문자열로 연결 금지**.

**잘못된 예:**
```xml
<a:p>
  <a:r><a:rPr .../><a:t>Step 1: 첫 번째 작업. Step 2: 두 번째 작업.</a:t></a:r>
</a:p>
```

**올바른 예:**
```xml
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="ko-KR" sz="2799" b="1" .../><a:t>Step 1</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="ko-KR" sz="2799" .../><a:t>첫 번째 작업.</a:t></a:r>
</a:p>
```

원본 `<a:p>`에서 `<a:pPr>`을 복사하여 줄 간격 보존. 헤더에 `b="1"` 적용.

### 스마트 따옴표

unpack/pack이 자동 처리. 단, Edit 도구는 스마트 따옴표를 ASCII로 변환.

**새 텍스트에 따옴표 추가 시 XML 엔티티 사용:**

```xml
<a:t>&#x201C;계약서&#x201D;</a:t>
```

| 문자 | 이름 | 유니코드 | XML 엔티티 |
|------|------|---------|-----------|
| `"` | 왼쪽 큰따옴표 | U+201C | `&#x201C;` |
| `"` | 오른쪽 큰따옴표 | U+201D | `&#x201D;` |
| `'` | 왼쪽 작은따옴표 | U+2018 | `&#x2018;` |
| `'` | 오른쪽 작은따옴표 | U+2019 | `&#x2019;` |

### 기타

- **공백**: 앞뒤 공백이 있는 `<a:t>`에 `xml:space="preserve"` 사용
- **XML 파싱**: `xml.etree.ElementTree` 대신 `defusedxml.minidom` 사용 (네임스페이스 손상 방지)
