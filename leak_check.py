#!/usr/bin/env python3
"""익명화 점검: 공개 GitHub Pages로 나가는 파일에 개인 식별 정보가 섞였는지 봅니다.

사용: python3 leak_check.py            (work/macmini-hub 에서)
      문제가 있으면 종료코드 1, 없으면 0
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
FILES = ["index.html", "hub.html", "data.json", "README.md", "manifest.webmanifest"]

# 직장·거주지·실명·소득·시드·지인 핸들 — 공개 금지
FORBIDDEN = [
    (r"기아", "직장명(기아)"),
    (r"삼성SDI|삼성\s?SDI|삼성전자", "직장명(삼성SDI/전자)"),
    (r"하이닉스", "직장명(SK하이닉스)"),
    (r"현대차|현대자동차", "직장명(현대차)"),
    (r"오토랜드", "직장명(오토랜드)"),
    (r"성내동|소하동|강동구|광명시", "거주지·사업장 상세"),
    (r"백재민|재민", "개인 실명"),
    (r"4,?959|49,?591", "근로소득 금액"),
    (r"3,?000만|시드 3", "시드 금액"),
    (r"정건|kun1632|jeonggeon", "지인 실명·핸들"),
    (r"117-29|4,157,626", "주소·소득 상세"),
    (r"010-?\d{4}-?\d{4}", "전화번호"),
    (r"[\w.+-]+@(?:naver|gmail)\.com", "이메일 주소"),
]

fails = []
for name in FILES:
    p = HERE / name
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    for pat, label in FORBIDDEN:
        for m in re.finditer(pat, text):
            line = text.count("\n", 0, m.start()) + 1
            fails.append(f"{name}:{line} {label} → {m.group(0)}")

if fails:
    print("익명화 점검 실패 — 아래를 지우고 다시 배포하세요")
    for f in fails:
        print("  -", f)
    sys.exit(1)

print("익명화 점검 통과 — 직장명·거주지·실명·소득·시드·지인 핸들 없음 (%d개 파일)" % len(FILES))
