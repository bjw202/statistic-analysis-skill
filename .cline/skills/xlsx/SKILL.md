---
name: xlsx
description: 스프레드시트 파일이 입력이나 출력일 때 사용. .xlsx/.xlsm/.csv/.tsv 파일 열기·읽기·편집·수정(컬럼 추가, 수식 계산, 서식, 차트, 데이터 정리), 새 스프레드시트 생성, 형식 변환, 지저분한 표 형식 데이터 정리. 파일명이나 경로가 언급될 때 트리거. Word 문서·HTML 보고서·단독 Python 스크립트·데이터베이스 파이프라인·Google Sheets API 작업에는 사용하지 말 것. Use when: xlsx, excel, 엑셀, 스프레드시트, spreadsheet, xls, xlsm, csv, tsv, 표, 데이터, 수식, 차트, 재무모델, financial model, openpyxl, pandas, 셀, 시트, 워크북, 엑셀 만들기, 엑셀 편집, 엑셀 읽기
---

# XLSX 스킬

## 작업 유형 판단표

| 작업 | 접근 방식 |
| --- | --- |
| 데이터 분석·조회·통계 | pandas 사용 (아래 [데이터 분석](#%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%B6%84%EC%84%9D) 참조) |
| 수식·서식·차트 생성 | openpyxl 사용 (아래 [파일 생성·편집](#%ED%8C%8C%EC%9D%BC-%EC%83%9D%EC%84%B1%ED%8E%B8%EC%A7%91) 참조) |
| 수식 재계산 (필수) | `python .cline/skills/xlsx/scripts/recalc.py output.xlsx` |
| 기존 파일 수정 | openpyxl `load_workbook` 사용 |

---

## 출력 요구사항 (필수)

### 모든 Excel 파일

- **전문 폰트**: Arial, Times New Roman 등 일관된 폰트 사용
- **수식 오류 ZERO**: `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?` 오류 없이 납품
- **템플릿 보존**: 기존 파일 수정 시 형식·스타일·관례를 정확히 따름. 기존 템플릿 규칙이 이 가이드라인보다 우선

### 재무 모델 색상 규칙

업계 표준 색상 코딩 (기존 템플릿이 없을 때):

| 색상 | RGB | 용도 |
| --- | --- | --- |
| 파란 텍스트 | `(0,0,255)` | 하드코딩 입력값, 사용자가 바꾸는 숫자 |
| 검정 텍스트 | `(0,0,0)` | 모든 수식과 계산 |
| 초록 텍스트 | `(0,128,0)` | 같은 워크북 내 다른 시트에서 가져오는 링크 |
| 빨간 텍스트 | `(255,0,0)` | 다른 파일 외부 링크 |
| 노란 배경 | `(255,255,0)` | 주목 필요한 주요 가정 셀 |

### 재무 모델 숫자 서식

| 항목 | 서식 |
| --- | --- |
| 연도 | 텍스트 문자열 ("2024", "2,024" 아님) |
| 통화 | `$#,##0` — 헤더에 단위 명시 ("Revenue ($mm)") |
| 0값 | `-`로 표시 (`$#,##0;($#,##0);-`) |
| 퍼센트 | `0.0%` (소수점 한 자리) |
| 배수 | `0.0x` (EV/EBITDA, P/E 등) |
| 음수 | 괄호 표기 `(123)`, 마이너스 `-123` 금지 |

---

## 핵심 원칙: 수식 vs 하드코딩

**항상 Excel 수식 사용. Python에서 계산해 결과를 하드코딩하지 말 것.**

```python
# 잘못된 방법 — Python에서 계산 후 하드코딩
total = df['Sales'].sum()
sheet['B10'] = total          # 5000을 하드코딩

# 올바른 방법 — Excel이 계산
sheet['B10'] = '=SUM(B2:B9)'
sheet['C5'] = '=(C4-C2)/C2'  # 성장률
sheet['D20'] = '=AVERAGE(D2:D19)'
```

모든 합계·퍼센트·비율·차이에 적용. 스프레드시트는 원본 데이터가 바뀌면 재계산할 수 있어야 함.

---

## 데이터 분석

분석·시각화·대량 작업에는 pandas 사용:

```python
import pandas as pd

# Excel 읽기
df = pd.read_excel('file.xlsx')                           # 첫 번째 시트
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # 모든 시트 (dict)

# 데이터 확인
df.head()       # 미리보기
df.info()       # 컬럼 정보
df.describe()   # 통계

# 쓰기
df.to_excel('output.xlsx', index=False)
```

**pandas 모범 사례:**

- 데이터 타입 명시: `pd.read_excel('file.xlsx', dtype={'id': str})`
- 특정 컬럼만 읽기: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- 날짜 처리: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`
- NaN 처리: `pd.notna()`로 확인

---

## 파일 생성·편집

수식·서식·Excel 기능에는 openpyxl 사용:

### 새 파일 생성

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# 데이터 추가
sheet['A1'] = '헤더'
sheet.append(['행', '데이터', '입력'])

# 수식
sheet['B10'] = '=SUM(B2:B9)'

# 서식
sheet['A1'].font = Font(bold=True, color='000000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# 컬럼 너비
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### 기존 파일 편집

```python
from openpyxl import load_workbook

# 기존 파일 로드 (수식 보존)
wb = load_workbook('existing.xlsx')
sheet = wb['시트명']  # 또는 wb.active

# 여러 시트 순회
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]

# 수정
sheet['A1'] = '새 값'
sheet.insert_rows(2)   # 2행에 행 삽입
sheet.delete_cols(3)   # 3번째 컬럼 삭제

# 새 시트 추가
new_sheet = wb.create_sheet('NewSheet')

wb.save('modified.xlsx')
```

**openpyxl 주의사항:**

- 셀 인덱스는 1-based (row=1, column=1 → A1)
- `data_only=True`로 열면 계산된 값 읽기 가능하지만 저장하면 수식이 영구 삭제됨
- 수식은 문자열로 저장됨 — 값 반영은 recalc.py 필수

---

## 수식 재계산 (수식 사용 시 필수)

openpyxl이 생성한 파일의 수식은 문자열로 저장되며 계산값이 없음. recalc.py로 LibreOffice를 통해 재계산:

```bash
python .cline/skills/xlsx/scripts/recalc.py output.xlsx
# 또는 타임아웃 지정
python .cline/skills/xlsx/scripts/recalc.py output.xlsx 30
```

스크립트 동작:

- 최초 실행 시 LibreOffice 매크로 자동 설정
- 모든 시트의 수식 재계산
- 전체 셀 오류 스캔 (`#REF!`, `#DIV/0!` 등)
- JSON으로 상세 오류 위치 반환

### recalc.py 출력 해석

```json
{
  "status": "success",        // 또는 "errors_found"
  "total_errors": 0,
  "total_formulas": 42,
  "error_summary": {          // 오류 있을 때만
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

`status`가 `errors_found`이면 `error_summary`로 위치 확인 후 수정하고 재실행.

---

## 수식 검증 체크리스트

### 필수 확인

- [ ] 샘플 참조 2-3개 테스트 — 전체 모델 전에 올바른 값을 가져오는지 확인

- [ ] 컬럼 매핑 확인 — 컬럼 64 = BL (BK 아님)

- [ ] 행 오프셋 — Excel 행은 1-indexed (DataFrame 행 5 = Excel 행 6)

### 자주 발생하는 실수

- [ ] NaN 처리 — `pd.notna()`로 null 값 확인

- [ ] 오른쪽 끝 컬럼 — FY 데이터가 50번 이상 컬럼에 있는 경우

- [ ] 중복 매칭 — 첫 번째뿐 아니라 모든 발생 위치 검색

- [ ] 0으로 나누기 — 수식에서 분모 사전 확인 (`#DIV/0!`)

- [ ] 잘못된 참조 — 모든 셀 참조가 의도한 셀을 가리키는지 확인 (`#REF!`)

- [ ] 크로스시트 참조 — 올바른 형식 사용 (`Sheet1!A1`)

### 수식 테스트 전략

- [ ] 작게 시작 — 광범위 적용 전 2-3 셀에서 수식 테스트

- [ ] 종속성 확인 — 수식에서 참조하는 모든 셀 존재 여부 확인

- [ ] 엣지케이스 테스트 — 0, 음수, 매우 큰 값 포함

---

## 가정(Assumptions) 문서화

하드코딩 값에는 반드시 주석 또는 인접 셀에 출처 명시:

```
형식: Source: [시스템/문서], [날짜], [참조], [URL]
예시: Source: Company 10-K, FY2024, Page 45, Revenue Note
     Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity
```

수식 내 가정은 별도 가정 셀에 배치하고 셀 참조 사용:

```python
# 잘못된 방법
sheet['B5'] = '=B4*1.05'          # 5%를 하드코딩

# 올바른 방법
sheet['B1'] = 0.05                # 가정 셀
sheet['B5'] = '=B4*(1+$B$1)'     # 가정 셀 참조
```

---

## 라이브러리 선택 기준

| 라이브러리 | 적합한 용도 |
| --- | --- |
| pandas | 데이터 분석, 대량 연산, 단순 데이터 내보내기 |
| openpyxl | 복잡한 서식, 수식, Excel 특화 기능 |

---

## 코드 스타일

- **간결하게**: 불필요한 주석, 중복 연산, print문 금지
- **Excel 파일**: 복잡한 수식이나 중요 가정 셀에 주석 추가
- **데이터 출처**: 하드코딩 값에 출처 문서화

---

## 의존성

```bash
pip install pandas openpyxl
# LibreOffice — 수식 재계산용 (recalc.py가 자동 설정)
```