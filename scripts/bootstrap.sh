#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-}"
if [ -z "$REPO_URL" ]; then
  echo "用法: ./scripts/bootstrap.sh <your-empty-github-repo-url>"
  exit 1
fi

git init
git remote add origin "$REPO_URL"
git add .
git commit -m "init: ai intelligence hub with alerts + actions"
git branch -M main || true
git push -u origin main
echo "✅ 已推送到 $REPO_URL"
