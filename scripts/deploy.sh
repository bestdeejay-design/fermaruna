#!/usr/bin/env bash
# Деплой фермы «Рунская» на SpaceWeb. Правила и полная процедура — DEPLOY.md.
# Использование: scripts/deploy.sh [--yes]
set -euo pipefail

REMOTE="${REMOTE:-sweb-fermaruna}"       # SSH-алиас из ~/.ssh/config
ROOT="${ROOT:-fermaruna_ru/public_html}" # веб-корень fermaruna.ru на сервере
BASE="${BASE:-https://fermaruna.ru}"     # канонический адрес боевой сборки

cd "$(dirname "$0")/.."

echo "── 1/4 Сборка (канон: $BASE)"
SITE_BASE_URL="$BASE" python3 scripts/build.py | tail -2

echo "── 2/4 Dry-run (что изменится на сервере)"
rsync -avn --exclude='.git' --exclude='config.php' ./ "$REMOTE:$ROOT/" | tail -4

if [ "${1:-}" != "--yes" ]; then
  printf "Выложить на %s:%s? [y/N] " "$REMOTE" "$ROOT"
  read -r answer
  case "$answer" in y|Y|да|Д) ;; *) echo "Отменено."; exit 0;; esac
fi

echo "── 3/4 Выкладка"
rsync -av --exclude='.git' --exclude='config.php' ./ "$REMOTE:$ROOT/"

echo "── 4/4 Проверка живого сайта"
fail=0
for p in "" "articles/" "plan.html" "staffhouse.html"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/$p")
  echo "  $BASE/$p -> $code"
  [ "$code" = "200" ] || fail=1
done
articles=$(curl -s "$BASE/articles/" | grep -o 'articles/[a-z0-9-]*/' | sort -u | wc -l | tr -d ' ')
echo "  статей в журнале: $articles"
[ "$fail" = "0" ] || { echo "⚠ Есть проблемы — проверить вручную (DEPLOY.md, раздел 4)"; exit 1; }
echo "Готово: сайт опубликован и проверен."
