#!/bin/sh
# AI 본부 관제 허브 배포 — build 후 저장소(woals193132-sys/macmini-hub) main 으로 밀어 넣고 Pages 상태를 확인합니다.
# 사용: sh deploy.sh            (work/macmini-hub 에서 실행)
set -e
REPO="woals193132-sys/macmini-hub"
MSG="${1:-AI 본부 관제 허브 v4 — 오늘의 실전 보드}"

cd "$(dirname "$0")"
python3 build.py
python3 render_check.py index.html --brief > /dev/null
python3 render_check.py hub.html --brief > /dev/null

# 매번 새 작업 폴더에 클론합니다 (이전 폴더가 잠겨 있어도 배포가 막히지 않게)
rm -rf repo 2>/dev/null || true
WORK=".deploy-$(date +%s)"
rm -rf "$WORK" 2>/dev/null || true
mkdir -p "$WORK"
git clone -q "https://github.com/${REPO}.git" "$WORK/repo"
cp index.html data.json manifest.webmanifest icon-180.png icon-512.png hub.html README.md build.py render_check.py deploy.sh .nojekyll "$WORK/repo/"
cd "$WORK/repo"
git add -A
if git diff --cached --quiet; then
  echo "변경 없음 — 커밋 생략"
else
  git -c user.name="맥미니" -c user.email="macmini@users.noreply.github.com" commit -q -m "$MSG"
  git push -q origin HEAD:main
  echo "push 완료: $(git log --oneline -1)"
fi

# GitHub Pages 소스 확인 (이미 켜져 있으면 그대로 둡니다)
gh api "repos/${REPO}/pages" --jq '.source.branch + " " + .source.path + " · " + .status' 2>/dev/null || \
  echo "!! Pages 상태를 읽지 못했습니다 — Settings → Pages → Source: Deploy from a branch → main / (root)"

cd ../..
rm -rf "$WORK" 2>/dev/null || true
echo "https://woals193132-sys.github.io/macmini-hub/"
