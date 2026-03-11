# PptxGenJS 가이드 — 처음부터 생성

템플릿이나 참조 프레젠테이션이 없을 때 사용.

---

## 설치 및 기본 구조

```javascript
const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';  // 또는 'LAYOUT_16x10', 'LAYOUT_4x3', 'LAYOUT_WIDE'
pres.author = '작성자';
pres.title = '프레젠테이션 제목';

let slide = pres.addSlide();
slide.addText("Hello World!", { x: 0.5, y: 0.5, fontSize: 36, color: "363636" });

pres.writeFile({ fileName: "Presentation.pptx" });
```

## 레이아웃 치수 (단위: 인치)

- `LAYOUT_16x9`: 10" × 5.625" (기본값)
- `LAYOUT_16x10`: 10" × 6.25"
- `LAYOUT_4x3`: 10" × 7.5"
- `LAYOUT_WIDE`: 13.3" × 7.5"

---

## 텍스트 및 서식

```javascript
// 기본 텍스트
slide.addText("Simple Text", {
  x: 1, y: 1, w: 8, h: 2, fontSize: 24, fontFace: "Arial",
  color: "363636", bold: true, align: "center", valign: "middle"
});

// 글자 간격 (charSpacing 사용 — letterSpacing은 무시됨)
slide.addText("SPACED TEXT", { x: 1, y: 1, w: 8, h: 1, charSpacing: 6 });

// 리치 텍스트 배열
slide.addText([
  { text: "굵게 ", options: { bold: true } },
  { text: "기울임 ", options: { italic: true } }
], { x: 1, y: 3, w: 8, h: 1 });

// 여러 줄 텍스트 (breakLine: true 필수)
slide.addText([
  { text: "1행", options: { breakLine: true } },
  { text: "2행", options: { breakLine: true } },
  { text: "3행" }  // 마지막 항목은 breakLine 불필요
], { x: 0.5, y: 0.5, w: 8, h: 2 });

// 텍스트 박스 내부 여백
slide.addText("제목", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  margin: 0  // 도형·아이콘과 정확히 정렬할 때 0 사용
});
```

**팁:** 텍스트 박스는 기본 내부 여백이 있음. 도형·선·아이콘과 정확히 정렬하려면 `margin: 0` 설정.

---

## 목록 및 불릿

```javascript
// 올바른 방법
slide.addText([
  { text: "첫 번째 항목", options: { bullet: true, breakLine: true } },
  { text: "두 번째 항목", options: { bullet: true, breakLine: true } },
  { text: "세 번째 항목", options: { bullet: true } }
], { x: 0.5, y: 0.5, w: 8, h: 3 });

// 잘못된 방법: 유니코드 불릿 절대 사용 금지
slide.addText("• 첫 번째 항목", { ... });  // 이중 불릿 발생

// 들여쓰기 및 번호 목록
{ text: "하위 항목", options: { bullet: true, indentLevel: 1 } }
{ text: "첫 번째", options: { bullet: { type: "number" }, breakLine: true } }
```

---

## 도형

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.8, w: 1.5, h: 3.0,
  fill: { color: "FF0000" }, line: { color: "000000", width: 2 }
});

slide.addShape(pres.shapes.OVAL, { x: 4, y: 1, w: 2, h: 2, fill: { color: "0000FF" } });

slide.addShape(pres.shapes.LINE, {
  x: 1, y: 3, w: 5, h: 0, line: { color: "FF0000", width: 3, dashType: "dash" }
});

// 투명도 적용
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "0088CC", transparency: 50 }
});

// 그림자 (올바른 방법)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 }
});
```

### 그림자 옵션

| 속성 | 타입 | 범위 | 비고 |
|------|------|------|------|
| `type` | string | `"outer"`, `"inner"` | |
| `color` | string | 6자리 hex | `#` 접두사 없음, 8자리 hex 금지 |
| `blur` | number | 0-100 pt | |
| `offset` | number | 0-200 pt | **음수 금지** — 파일 손상 |
| `angle` | number | 0-359도 | 135=오른쪽 아래, 270=위쪽 |
| `opacity` | number | 0.0-1.0 | 투명도는 반드시 이 속성으로 |

위쪽 그림자 (푸터 바 위에): `angle: 270` + 양수 offset — **음수 offset 금지**.

---

## 이미지

### 소스 유형

```javascript
// 파일 경로
slide.addImage({ path: "images/chart.png", x: 1, y: 1, w: 5, h: 3 });

// URL
slide.addImage({ path: "https://example.com/image.jpg", x: 1, y: 1, w: 5, h: 3 });

// base64 (빠름, 파일 I/O 없음)
slide.addImage({ data: "image/png;base64,iVBORw0KGgo...", x: 1, y: 1, w: 5, h: 3 });
```

### 이미지 옵션

```javascript
slide.addImage({
  path: "image.png",
  x: 1, y: 1, w: 5, h: 3,
  rotate: 45,              // 0-359도
  rounding: true,          // 원형 크롭
  transparency: 50,        // 0-100
  flipH: true,             // 수평 반전
  altText: "설명",          // 접근성
  hyperlink: { url: "https://example.com" }
});
```

### 크기 모드

```javascript
// Contain - 비율 유지, 안에 맞춤
{ sizing: { type: 'contain', w: 4, h: 3 } }

// Cover - 비율 유지, 채우기 (크롭 가능)
{ sizing: { type: 'cover', w: 4, h: 3 } }

// Crop - 특정 부분 자르기
{ sizing: { type: 'crop', x: 0.5, y: 0.5, w: 2, h: 2 } }
```

### 비율 유지 치수 계산

```javascript
const origWidth = 1978, origHeight = 923, maxHeight = 3.0;
const calcWidth = maxHeight * (origWidth / origHeight);
const centerX = (10 - calcWidth) / 2;

slide.addImage({ path: "image.png", x: centerX, y: 1.2, w: calcWidth, h: maxHeight });
```

---

## 아이콘

react-icons로 SVG 아이콘 생성 후 PNG로 래스터화.

### 설치

```bash
npm install -g react-icons react react-dom sharp
```

### 구현

```javascript
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaCheckCircle } = require("react-icons/fa");

function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// 슬라이드에 추가
const iconData = await iconToBase64Png(FaCheckCircle, "#4472C4", 256);
slide.addImage({ data: iconData, x: 1, y: 1, w: 0.5, h: 0.5 });
```

**주의:** size 256 이상 사용 — 렌더링 해상도. 슬라이드 표시 크기는 `w`, `h`(인치)로 설정.

### 아이콘 라이브러리

- `react-icons/fa` - Font Awesome
- `react-icons/md` - Material Design
- `react-icons/hi` - Heroicons
- `react-icons/bi` - Bootstrap Icons

---

## 배경

```javascript
// 단색
slide.background = { color: "F1F1F1" };

// 이미지 (URL)
slide.background = { path: "https://example.com/bg.jpg" };

// 이미지 (base64)
slide.background = { data: "image/png;base64,iVBORw0KGgo..." };
```

---

## 표

```javascript
slide.addTable([
  ["헤더 1", "헤더 2"],
  ["셀 1", "셀 2"]
], {
  x: 1, y: 1, w: 8, h: 2,
  border: { pt: 1, color: "999999" }, fill: { color: "F1F1F1" }
});

// 셀 병합 포함 고급 표
let tableData = [
  [{ text: "헤더", options: { fill: { color: "6699CC" }, color: "FFFFFF", bold: true } }, "셀"],
  [{ text: "병합", options: { colspan: 2 } }]
];
slide.addTable(tableData, { x: 1, y: 3.5, w: 8, colW: [4, 4] });
```

---

## 차트

```javascript
// 막대 차트
slide.addChart(pres.charts.BAR, [{
  name: "매출", labels: ["Q1", "Q2", "Q3", "Q4"], values: [4500, 5500, 6200, 7100]
}], {
  x: 0.5, y: 0.6, w: 6, h: 3, barDir: 'col',
  showTitle: true, title: '분기별 매출'
});

// 선 차트
slide.addChart(pres.charts.LINE, [{
  name: "온도", labels: ["1월", "2월", "3월"], values: [32, 35, 42]
}], { x: 0.5, y: 4, w: 6, h: 3, lineSize: 3, lineSmooth: true });

// 원형 차트
slide.addChart(pres.charts.PIE, [{
  name: "점유율", labels: ["A", "B", "기타"], values: [35, 45, 20]
}], { x: 7, y: 1, w: 5, h: 4, showPercent: true });
```

### 세련된 차트 스타일

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",

  // 발표 팔레트에 맞는 커스텀 색상
  chartColors: ["0D9488", "14B8A6", "5EEAD4"],

  // 깔끔한 배경
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },

  // 부드러운 축 라벨
  catAxisLabelColor: "64748B",
  valAxisLabelColor: "64748B",

  // 값 축만 미세한 격자선
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },

  // 막대 위 데이터 라벨
  showValue: true,
  dataLabelPosition: "outEnd",
  dataLabelColor: "1E293B",

  // 단일 시리즈는 범례 숨기기
  showLegend: false,
});
```

**주요 스타일 옵션:**
- `chartColors: [...]` - 시리즈/세그먼트 hex 색상
- `chartArea: { fill, border, roundedCorners }` - 차트 배경
- `catGridLine/valGridLine: { color, style, size }` - 격자선 (`style: "none"`으로 숨기기)
- `lineSmooth: true` - 곡선 (선 차트)
- `legendPos: "r"` - 범례 위치: "b", "t", "l", "r", "tr"

---

## 슬라이드 마스터

```javascript
pres.defineSlideMaster({
  title: 'TITLE_SLIDE', background: { color: '283A5E' },
  objects: [{
    placeholder: { options: { name: 'title', type: 'title', x: 1, y: 2, w: 8, h: 2 } }
  }]
});

let titleSlide = pres.addSlide({ masterName: "TITLE_SLIDE" });
titleSlide.addText("제목", { placeholder: "title" });
```

---

## 자주 발생하는 오류

1. **hex 색상에 "#" 절대 사용 금지** — 파일 손상
   ```javascript
   color: "FF0000"   // 올바름
   color: "#FF0000"  // 잘못됨
   ```

2. **hex 색상 문자열에 불투명도 인코딩 금지** — 8자리 hex는 파일 손상
   ```javascript
   shadow: { color: "00000020" }                    // 잘못됨 — 파일 손상
   shadow: { color: "000000", opacity: 0.12 }       // 올바름
   ```

3. **`bullet: true` 사용** — 유니코드 "•" 절대 사용 금지 (이중 불릿 발생)

4. **배열 항목 간 `breakLine: true` 사용**

5. **불릿과 `lineSpacing` 같이 사용 금지** — 과도한 간격 발생. 대신 `paraSpaceAfter` 사용

6. **프레젠테이션 인스턴스 재사용 금지** — `pptxgen()` 객체를 재사용하지 말 것

7. **옵션 객체 공유 금지** — PptxGenJS가 객체를 내부적으로 수정(EMU 변환)하므로 여러 호출에 같은 객체 공유하면 두 번째 도형이 손상됨
   ```javascript
   // 잘못됨: 같은 shadow 객체 공유
   const shadow = { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 };
   slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });
   slide.addShape(pres.shapes.RECTANGLE, { shadow, ... }); // 두 번째에서 이미 변환된 값 사용

   // 올바름: 매번 새 객체 생성
   const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
   slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
   slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
   ```

8. **`ROUNDED_RECTANGLE`에 직사각형 강조 보더 사용 금지** — 둥근 모서리를 커버하지 못함. 대신 `RECTANGLE` 사용

---

## 빠른 참조

- **도형**: RECTANGLE, OVAL, LINE, ROUNDED_RECTANGLE
- **차트**: BAR, LINE, PIE, DOUGHNUT, SCATTER, BUBBLE, RADAR
- **레이아웃**: LAYOUT_16x9 (10"×5.625"), LAYOUT_16x10, LAYOUT_4x3, LAYOUT_WIDE
- **정렬**: "left", "center", "right"
- **차트 데이터 라벨**: "outEnd", "inEnd", "center"
