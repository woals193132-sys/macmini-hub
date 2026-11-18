#!/bin/sh
# AI 본부 관제 허브 배포 — 저장소가 공개 + Pickle 앱 접근 허용된 뒤 한 번만 실행하면 됩니다.
# 사용: sh deploy.sh            (work/macmini-hub 에서 실행)
set -e
REPO="woals193132-sys/macmini-hub"

cd "$(dirname "$0")"
python3 build.py
rm -rf repo
git clone "https://github.com/${REPO}.git" repo
cp index.html data.json manifest.webmanifest icon-180.png icon-512.png hub.html README.md .nojekyll repo/
cd repo
git add -A
git -c user.name="맥미니" -c user.email="macmini@users.noreply.github.com" commit -m "AI 본부 관제 허브 v2 (1실 6그룹 조직도)"
git push origin HEAD:main

# GitHub Pages 켜기 (권한이 없으면 Settings → Pages 에서 main / (root) 를 고르면 됩니다)
gh api -X POST "repos/${REPO}/pages" -f "source[branch]=main" -f "source[path]=/" 2>/dev/null || \
  gh api -X PUT "repos/${REPO}/pages" -f "source[branch]=main" -f "source[path]=/" 2>/dev/null || \
  echo "!! Pages 자동 활성화 실패 — Settings → Pages → Source: Deploy from a branch → main / (root)"

echo "https://woals193132-sys.github.io/macmini-hub/"
