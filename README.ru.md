![Ферма Рунская](assets/header.svg)

# Ферма «Рунская»

Статический сайт натурального хозяйства «Рунская» в верховьях Волги, Тверская область. Картофель с целины, мёд с собственной пасеки, яйцо и птица на зерне и траве.

**🌐 Версии:** [English](README.md) · [Русский](README.ru.md) · [Сайт](http://fermaruna.ru)

Сайт: [http://fermaruna.ru](http://fermaruna.ru) · Зеркало GitHub Pages: [https://bestdeejay-design.github.io/fermaruna/](https://bestdeejay-design.github.io/fermaruna/)

📖 План развития хозяйства: [docs/PLAN.md](docs/PLAN.md) — от идеи до самофинансируемой фермы.
🌐 Онлайн-чтение (HTML, GitHub Pages): [plan.html](https://bestdeejay-design.github.io/fermaruna/plan.html) — план, аудит и шаг 1 по 1500 га на одной странице.

Язык сайта: русский.

## Что это

Небольшой статический сайт: главная, о ферме, хроника новостей, журнал статей, политика конфиденциальности, своя страница 404. Контент хранится в JSON, HTML собирает Python-скрипт, на выходе обычные файлы, которые отдаёт Apache. Форма связи отправляет заявки на небольшой PHP-обработчик.

Продукция на сайте: картофель, мёд, столовое яйцо, мясо птицы, суточные и подрощенные птенцы.

## Стек

- Генератор: только стандартная библиотека Python 3 ([scripts/build.py](scripts/build.py), без зависимостей)
- Фронтенд: чистые HTML/CSS/JS ([assets/css/main.css](assets/css/main.css), [assets/js/main.js](assets/js/main.js))
- Шрифты: Alegreya + Manrope, woff2 с кириллическими подмножествами ([assets/fonts/](assets/fonts/))
- Изображения: адаптивные WebP-пары (640/1200px) плюс `og-cover.jpg` для соцсетей ([assets/img/](assets/img/))
- Конфиг сервера: Apache [`.htaccess`](.htaccess) (UTF-8, без листинга каталогов, сжатие, кэш в браузере, защитные заголовки)
- Обработчик формы: [`send.php`](send.php) с ловушкой для ботов, ограничением частоты и защитой от инъекций в заголовки; настройки берутся из `config.php`, которого нет в git (см. [`config.example.php`](config.example.php))
- PWA: [`manifest.webmanifest`](manifest.webmanifest), [`favicon.svg`](favicon.svg)

## Структура репозитория

```
content/        site.json, news.json, faq.json + articles/*.json
templates/      home.html, about.html, privacy.html, 404.html
scripts/        build.py (единственный шаг сборки)
assets/         css/, js/, img/, fonts/, header.svg, footer.svg
about/ news/ articles/ privacy/   сгенерированные страницы (результат, закоммичен)
index.html 404.html robots.txt sitemap.xml  сгенерированные файлы (результат, закоммичен)
.htaccess send.php config.example.php manifest.webmanifest favicon.svg
docs/           рукописные документы проекта (план развития хозяйства)
```

Источники правды: [`content/site.json`](content/site.json) (название, контакты, адрес, ссылка на карту), `content/news.json`, `content/faq.json`, JSON-файлы статей. Шаблоны в [`templates/`](templates/) используют `{{токены}}` из функции `render_tokens()`.

## Сборка

```bash
python3 scripts/build.py
```

По умолчанию канонический адрес указывает на Pages. Для боевого домена:

```bash
SITE_BASE_URL=http://fermaruna.ru python3 scripts/build.py
```

Скрипт перезаписывает `index.html`, страницы разделов, `sitemap.xml`, `robots.txt`, `manifest.webmanifest` и `SEO_PLAN.md`. Телефон и почта берутся из `content/site.json`.

## Публикация

Собрать, затем загрузить корень репозитория (статический результат) на Apache-хостинг с PHP 8.1. Общая схема:

```bash
python3 scripts/build.py
rsync -av --exclude='.git' ./ user@host:/path/to/www/
```

Скопировать `config.example.php` в `config.php` на сервере и вписать адрес для заявок. CI не настроен, публикация вручную.

## Обработчик формы

[`send.php`](send.php) принимает только `POST`, ждёт `name`, `contact`, `consent` (плюс необязательные `product`, `message`), отвечает JSON. Без корректного `config.php` отвечает `503 not_configured`. На сервере ничего не хранится.

## Заметка про SEO

Канонический адрес `http://fermaruna.ru` (строка sitemap в `robots.txt` и canonical-теги в сгенерированном HTML). HTTPS пока не настроен, поэтому редирект на HTTPS в `.htaccess` остаётся закомментированным. Разметка: OG/Twitter-карточки, JSON-LD (LocalBusiness, FAQ, статьи, хлебные крошки), у каждой статьи своё описание, предупреждения о длине выводятся в лог сборки.

![подвал](assets/footer.svg)

#fermaruna #organic-farm #tver-region #static-site #python-stdlib #vanilla-js #apache #russian
