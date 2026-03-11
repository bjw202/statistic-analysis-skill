---
name: pptx
description: .pptx 파일이 관련된 모든 작업에 사용. 슬라이드 덱·발표자료·피치덱 생성, 기존 .pptx 읽기·파싱·텍스트 추출, 편집·수정·업데이트, 파일 합치기·분리, 템플릿·레이아웃·발표자 노트 작업. "deck", "slides", "presentation", .pptx 파일명 언급 시 트리거. Use when: pptx, ppt, 슬라이드, 발표자료, 프레젠테이션, 덱, 피치덱, 파워포인트, presentation, slides, deck, pitch deck, powerpoint, slide deck, 슬라이드 만들기, 발표 자료 만들기, pptx 편집, pptx 생성, pptx 읽기
---

# PPTX 스킬

## 작업 유형 판단표

| 작업 | 이동할 문서 |
| --- | --- |
| 내용 읽기/분석 | 아래 [읽기 섹션](#%EC%9D%BD%EA%B8%B0) 참조 |
| 템플릿 기반 편집/생성 | `docs/editing.md` |
| 처음부터 생성 (템플릿 없음) | `docs/pptxgenjs.md` |

---

## 빠른 참조

| 작업 | 명령어 |
| --- | --- |
| 텍스트 추출 | `python -m markitdown presentation.pptx` |
| 슬라이드 썸네일 | `python .cline/skills/pptx/scripts/thumbnail.py presentation.pptx` |
| XML 원문 추출 | `python .cline/skills/pptx/scripts/office/unpack.py presentation.pptx unpacked/` |

---

## 읽기

```bash
# 텍스트 추출
python -m markitdown presentation.pptx

# 슬라이드 썸네일 그리드 생성
python .cline/skills/pptx/scripts/thumbnail.py presentation.pptx

# 원시 XML 추출
python .cline/skills/pptx/scripts/office/unpack.py presentation.pptx unpacked/
```

---

## 디자인 가이드

**평범한 슬라이드는 금지.** 흰 배경에 불릿 텍스트만 있는 슬라이드는 인상을 주지 못한다.

### 시작 전

- **굵고 주제에 맞는 색상 팔레트 선정**: 색상을 다른 발표에 바꿔 넣어도 어울린다면 주제 특화 선택이 아님.
- **색상 비중**: 주 색상 60-70% + 보조 1-2개 + 강조 1개. 색상을 균등하게 배분하지 말 것.
- **명암 대비**: 제목/마무리 슬라이드는 어두운 배경, 내용 슬라이드는 밝은 배경 ("샌드위치"), 또는 전체 어두운 배경으로 프리미엄 느낌.
- **시각 모티프 통일**: 둥근 이미지 프레임, 원형 아이콘, 굵은 단측 보더 등 하나를 골라 모든 슬라이드에 적용.

### 색상 팔레트 예시

| 테마 | 주 색상 | 보조 색상 | 강조 색상 |
| --- | --- | --- | --- |
| Midnight Executive | `1E2761` (네이비) | `CADCFC` (아이스 블루) | `FFFFFF` |
| Forest & Moss | `2C5F2D` (포레스트) | `97BC62` (모스) | `F5F5F5` |
| Coral Energy | `F96167` (코랄) | `F9E795` (골드) | `2F3C7E` |
| Warm Terracotta | `B85042` (테라코타) | `E7E8D1` (샌드) | `A7BEAE` |
| Ocean Gradient | `065A82` (딥블루) | `1C7293` (틸) | `21295C` |
| Charcoal Minimal | `36454F` (차콜) | `F2F2F2` (오프화이트) | `212121` |

### 슬라이드별 구성

**모든 슬라이드에 시각 요소 필수** — 이미지, 차트, 아이콘, 도형 중 하나.

**레이아웃 옵션:**

- 2단 컬럼 (텍스트 좌 + 일러스트 우)
- 아이콘 + 텍스트 행 (색상 원 안 아이콘 + 굵은 헤더 + 설명)
- 2x2 또는 2x3 그리드
- 반 블리드 이미지 (좌/우 전체) + 내용 오버레이

**데이터 표시:**

- 대형 수치 콜아웃 (60-72pt 숫자 + 작은 라벨)
- 비교 컬럼 (before/after, pros/cons)
- 타임라인 또는 프로세스 흐름 (번호 단계, 화살표)

### 타이포그래피

| 헤더 폰트 | 본문 폰트 |
| --- | --- |
| Georgia | Calibri |
| Arial Black | Arial |
| Cambria | Calibri |
| Trebuchet MS | Calibri |

| 요소 | 크기 |
| --- | --- |
| 슬라이드 제목 | 36-44pt 볼드 |
| 섹션 헤더 | 20-24pt 볼드 |
| 본문 | 14-16pt |
| 캡션 | 10-12pt 흐림 |

### 간격

- 최소 여백: 0.5인치
- 콘텐츠 블록 간격: 0.3-0.5인치

### 금지 사항

- 동일 레이아웃 반복 — 컬럼, 카드, 콜아웃 변화 줄 것
- 본문 텍스트 가운데 정렬 — 단락/목록은 왼쪽 정렬, 제목만 가운데
- 크기 대비 부족 — 제목은 36pt+ 이상
- 파란색 기본값 — 주제에 맞는 색상 선택
- 텍스트만 있는 슬라이드 — 이미지·아이콘·차트·도형 추가
- **제목 아래 강조선 금지** — AI 생성 슬라이드의 대표 패턴, 여백이나 배경색으로 대체

---

## QA (필수)

**문제가 있다고 가정하고 찾아야 한다.** 첫 렌더링이 맞는 경우는 거의 없다.

### 내용 QA

```bash
python -m markitdown output.pptx
```

누락된 내용, 오탈자, 순서 오류 확인.

**템플릿 사용 시, 자리표시자 텍스트 잔류 확인:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

결과가 있으면 선언 전 수정.

### 시각 QA

슬라이드를 이미지로 변환 후 (아래 [이미지 변환](#%EC%9D%B4%EB%AF%B8%EC%A7%80-%EB%B3%80%ED%99%98) 참조) 다음 프롬프트로 검사:

```
이 슬라이드들을 시각적으로 검사해주세요. 문제가 있다고 가정하고 찾아주세요.

확인 사항:
- 겹치는 요소 (텍스트가 도형 위, 선이 단어 위, 쌓인 요소)
- 텍스트 넘침 또는 가장자리/박스 경계에서 잘림
- 장식 선이 한 줄 텍스트용인데 제목이 두 줄로 줄바꿈됨
- 출처 표기 또는 푸터가 위 내용과 충돌
- 너무 가까운 요소 (0.3인치 미만 간격) 또는 카드/섹션이 거의 닿음
- 불균일한 간격 (한쪽 넓고 다른 쪽 빡빡)
- 슬라이드 가장자리 여백 부족 (0.5인치 미만)
- 컬럼 또는 유사 요소 정렬 불일치
- 낮은 대비 텍스트 (크림 배경에 연회색 텍스트 등)
- 낮은 대비 아이콘 (어두운 배경에 어두운 아이콘)
- 너무 좁은 텍스트 박스로 인한 과도한 줄바꿈
- 자리표시자 내용 잔류

각 슬라이드의 문제 또는 우려 사항을 나열하세요 (사소한 것 포함).

1. /path/to/slide-01.jpg (예상: [간단한 설명])
2. /path/to/slide-02.jpg

모든 문제를 보고해주세요.
```

### 검증 루프

1. 슬라이드 생성 → 이미지 변환 → 검사
2. **발견된 문제 목록화** (없으면 더 꼼꼼히 재검사)
3. 문제 수정
4. **영향받은 슬라이드 재검증** — 하나 수정하면 다른 곳에 문제 생길 수 있음
5. 새 문제가 없을 때까지 반복

**수정-검증 사이클을 최소 1회 완료하기 전까지 완료 선언 금지.**

---

## 이미지 변환

```bash
python .cline/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

`slide-01.jpg`, `slide-02.jpg` 등이 생성됨.

수정 후 특정 슬라이드만 재렌더링:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## 의존성

```bash
pip install "markitdown[pptx]"   # 텍스트 추출
pip install Pillow               # 썸네일 그리드
npm install -g pptxgenjs         # 처음부터 생성 시
# LibreOffice (soffice) - PDF 변환
# Poppler (pdftoppm) - PDF → 이미지
```

---

## 스크립트 구조

이 스킬의 Python 스크립트는 `.cline/skills/pptx/scripts/`에 포함되어 있습니다.

```
scripts/
├── thumbnail.py          # 슬라이드 썸네일 그리드
├── add_slide.py          # 슬라이드 복제/추가
├── clean.py              # 고아 파일 정리
└── office/
    ├── unpack.py         # PPTX 압축 해제 + XML 포맷
    ├── pack.py           # PPTX 재패킹 + 검증
    ├── soffice.py        # LibreOffice 래퍼 (PDF 변환)
    ├── validate.py       # OOXML 스키마 검증
    ├── helpers/          # XML 처리 유틸리티
    └── validators/       # 파일 타입별 검증기
```