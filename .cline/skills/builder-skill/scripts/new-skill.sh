#!/bin/bash
# 용도: 새 Cline 스킬의 표준 디렉토리 구조를 생성합니다.
# 사용법: bash scripts/new-skill.sh {스킬명}
# 예시:  bash scripts/new-skill.sh my-new-skill
#
# 생성되는 구조:
# .cline/skills/{스킬명}/
# ├── SKILL.md
# ├── docs/
# └── scripts/

set -e

if [ -z "$1" ]; then
  echo "오류: 스킬명을 인수로 전달하세요."
  echo "사용법: bash scripts/new-skill.sh {스킬명}"
  exit 1
fi

SKILL_NAME="$1"
SKILL_DIR=".cline/skills/${SKILL_NAME}"
TEMPLATE_DIR="$(dirname "$0")/../templates/SKILL.md.template"

# 이미 존재하는지 확인
if [ -d "$SKILL_DIR" ]; then
  echo "오류: '${SKILL_DIR}' 디렉토리가 이미 존재합니다."
  exit 1
fi

# 디렉토리 생성
mkdir -p "${SKILL_DIR}/docs"
mkdir -p "${SKILL_DIR}/scripts"

# SKILL.md 템플릿 복사
if [ -f "$TEMPLATE_DIR" ]; then
  cp "$TEMPLATE_DIR" "${SKILL_DIR}/SKILL.md"
  echo "SKILL.md 템플릿을 복사했습니다."
else
  # 템플릿이 없으면 기본 SKILL.md 생성
  cat > "${SKILL_DIR}/SKILL.md" << 'EOF'
---
name: {스킬명}
description: {스킬 설명}. Use when: {키워드1}, {키워드2}, {키워드3}
---

# {스킬 제목}

---

## 핵심 절차

**Step 1: {첫 번째 단계}**

- {세부 항목}

**Step 2: {두 번째 단계}**

- {세부 항목}
EOF
  echo "기본 SKILL.md를 생성했습니다."
fi

echo ""
echo "✅ 스킬 디렉토리가 생성되었습니다: ${SKILL_DIR}"
echo ""
echo "다음 단계:"
echo "  1. ${SKILL_DIR}/SKILL.md 를 편집하여 frontmatter를 채우세요"
echo "  2. docs/ 폴더에 상세 가이드 문서를 추가하세요"
echo "  3. scripts/ 폴더에 실행 가능한 유틸리티 스크립트를 추가하세요"
echo ""
echo "가이드: .cline/skills/builder-skill/docs/skill-creation-guide.md"
