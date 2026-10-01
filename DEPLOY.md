# DEPLOY.md — деплой сайта фермы «Рунская» на хостинг

Процедура публикации сайта на живой хостинг **fermaruna.ru** (Apache, SpaceWeb) и проверки зеркала GitHub Pages.
Для агентов: короткая версия правил — в [AGENTS.md](AGENTS.md); эта страница — полная процедура.

---

## 1. Инфраструктура

| Компонент | Значение |
|---|---|
| Хостинг | SpaceWeb (shared), сервер `77.222.40.7` |
| SSH-алиас | `sweb-fermaruna` (в `~/.ssh/config`, ключ `~/.ssh/sweb_fermaruna_ed25519`) |
| Веб-корень fermaruna.ru | `~/fermaruna_ru/public_html` на сервере |
| Служебный `~/public_html` | **не трогать** — это другой виртуальный хост |
| `config.php` на сервере | настройки формы (`send.php`) — **никогда не перезаписывать и не удалять** (в репо только `config.example.php`) |
| Зеркало | GitHub Pages из ветки `main`, путь `/` — https://bestdeejay-design.github.io/fermaruna/ |
| Бэкапы на сервере | `~/public_html_old_*.tar.gz` — не удалять |

## 2. Сборка

Канонический адрес боевой сборки — **`https://fermaruna.ru`** (HTTPS, редирект настраивает `.htaccess` на сервере):

```bash
SITE_BASE_URL=https://fermaruna.ru python3 scripts/build.py
```

Сборка перезаписывает: `index.html`, `about/`, `news/`, `articles/`, `privacy/`, `404.html`, `sitemap.xml`, `robots.txt`, `manifest.webmanifest`, `SEO_PLAN.md`. Это сгенерированные файлы — коммитим как результат. В логе сборки: число статей журнала и предупреждения по длинам описаний.

Новые статьи журнала: добавить JSON-список в `content/articles/` (генератор читает все файлы папки), пересобрать.

## 3. Деплой

**Основной способ — автоматический (GitHub Actions):** при каждом пуше в `main` workflow `.github/workflows/deploy-hosting.yml` сам собирает сайт с боевым адресом, rsync-ом выкладывает на SpaceWeb и проверяет живые URL. Секреты репозитория: `DEPLOY_SSH_KEY` (выделенный ключ деплоя, не основной), `DEPLOY_HOST`, `DEPLOY_USER`. Статус: `gh run list --workflow=deploy-hosting.yml`. Ручной запуск: `gh workflow run deploy-hosting.yml --ref main`.

**Резервный способ — локальный скрипт** (если Actions недоступен): (сборка + dry-run + подтверждение + rsync + проверка URL):

```bash
./scripts/deploy.sh          # спросит подтверждение
./scripts/deploy.sh --yes    # без вопроса (для агентов: только если dry-run просмотрен)
```

**Ручной способ** (эквивалент):

```bash
# 1) Dry-run — посмотреть, что изменится (обязательно перед выкладкой)
rsync -avn --exclude='.git' --exclude='config.php' ./ sweb-fermaruna:fermaruna_ru/public_html/

# 2) Выкладка
rsync -av --exclude='.git' --exclude='config.php' ./ sweb-fermaruna:fermaruna_ru/public_html/
```

**Инварианты деплоя:**

1. **Без `--delete`.** На сервере есть файлы вне репо (`config.php`); синхронизация только аддитивная. Удаление файлов на сервере — отдельным осознанным шагом по списку.
2. **`config.php` исключён** из rsync всегда.
3. Сначала dry-run, затем выкладка.
4. `~/public_html` (без доменной папки) и бэкапы `*.tar.gz` на сервере не трогать.

## 4. Проверка после деплоя

```bash
for p in "" "articles/" "plan.html" "staffhouse.html" "articles/med-sorta/"; do
  curl -s -o /dev/null -w "https://fermaruna.ru/$p -> %{http_code}\n" "https://fermaruna.ru/$p"
done
curl -s https://fermaruna.ru/articles/ | grep -o 'articles/[a-z0-9-]*/' | sort -u | wc -l   # = число статей
curl -s https://fermaruna.ru/ | grep -o '<link rel="canonical"[^>]*>'                       # = https://fermaruna.ru/
```

Ожидаемо: все 200; число статей соответствует `content/articles/`; канонический адрес — `https://fermaruna.ru/`.

Состояние на 2026-10-01: 22 статьи, план развития (`plan.html`), эскиз стафф-хауса (`staffhouse.html`), карты района — опубликованы и на хостинге, и на Pages.

## 5. GitHub Pages (зеркало)

- Источник: ветка **`main`**, путь `/`. Статус: `gh api repos/bestdeejay-design/fermaruna/pages --jq '{branch: .source.branch, status: .status}'`.
- Пересборка (если нужно форсировать): `gh api -X POST repos/bestdeejay-design/fermaruna/pages/builds`.
- **Известный инцидент (2026-10-01):** источник Pages был переключён на служебную ветку `arena/…` → на зеркале 404 при живой главной. Лечение: `gh api -X PUT repos/bestdeejay-design/fermaruna/pages -f "source[branch]=main" -f "source[path]=/"`, затем POST builds. Если зеркало «откатилось» — первым делом проверять источник.
- Зеркало обновляется автоматически при пуше в `main` (задержка ~1–3 мин). Живой хостинг — **только ручным деплоем** (п. 3), CI не настроен.

## 6. Ветки и слияния

- `main` — источник публикации. Коммитить/мержить и сразу публиковать.
- `arena/*` — параллельные сессии. Перед слиянием: `git diff main...ветка --stat`; брать контент (статьи, JSON), сайт-файлы сверять с main (в arena-сборках встречались JS-base-хак, неконсистентные генераты, перекропленные фото; прецедент слияния — в истории git, 2026-10-01: 22 статьи).
- После слияний — пересборка (п. 2), деплой (п. 3), проверка (п. 4).

## 7. Откат

- Ровес: `git revert` проблемного коммита, пересборка, деплой.
- Сервер: последний полный бэкап — `~/public_html_old_20261001.tar.gz` на хостинге; распаковка на месте при необходимости (осторожно: он старее текущего состояния).
- Точечный откат файла: `git show <commit>:<path> > <path>` + деплой этого файла.
