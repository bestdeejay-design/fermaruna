#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор статического сайта «Ферма Рунская».

Использует только стандартную библиотеку Python 3.9+ — ничего устанавливать не нужно.

    python3 scripts/build.py

Что делает:
  * собирает главную, «О ферме», «Хронику», журнал (библиотека + статьи), политику и 404;
  * пишет sitemap.xml, robots.txt, manifest.webmanifest и SEO_PLAN.md;
  * подставляет адаптивные картинки (assets/img/<имя>-<ширина>.webp) с srcset.

Канонический адрес по умолчанию — GitHub Pages. Для боевого домена:

    SITE_BASE_URL=https://fermaruna.ru python3 scripts/build.py

Ссылки на страницах относительные, поэтому сайт работает и в подпапке (GitHub Pages),
и в корне домена, и просто из файловой системы.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
IMG_DIR = ROOT / "assets" / "img"

SITE_BASE = os.environ.get("SITE_BASE_URL", "https://bestdeejay-design.github.io/fermaruna/").rstrip("/") + "/"
TODAY = os.environ.get("CONTENT_DATE", "2026-10-01")

NBSP = "\u00a0"
WARNINGS: list[str] = []


# ───────────────────────────── утилиты ─────────────────────────────

def esc(value) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def asset_v(rel: str) -> str:
    """Короткий хеш файла — добавляется как ?v=… чтобы браузеры не держали устаревший CSS/JS."""
    f = ROOT / rel
    return hashlib.md5(f.read_bytes()).hexdigest()[:8] if f.exists() else "0"


MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def ru_date_short(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


# Типографика: неразрывные пробелы после коротких слов, перед тире, в «20 °C», «250 мл».
_TAG_RE = re.compile(r"(<[^>]+>)")
_SHORT_RE = re.compile(r"(?<![\wЁё-])([А-Яа-яЁё]{1,3})[ \t]+(?=[«\"(\wЁё])")
_UNIT_RE = re.compile(r"(\d)[ \t]+(?=(?:г|кг|мл|л|см|мм|м|км|°C|°С|%|шт|дн|дня|дней|мин|ч|час|часа|часов|суток|недель|недели|неделю|лет|года|год|мес|месяцев|₽|руб)(?![А-Яа-яЁё]))")


def typo_text(t: str) -> str:
    t = re.sub(r"[ \t]+—", NBSP + "—", t)
    t = _SHORT_RE.sub(lambda m: m.group(1) + NBSP, t)
    t = _UNIT_RE.sub(lambda m: m.group(1) + NBSP, t)
    return t


def typo_html(markup: str) -> str:
    out, skip = [], 0
    for part in _TAG_RE.split(markup):
        if part.startswith("<"):
            low = part.lower()
            if low.startswith(("<script", "<style")):
                skip += 1
            elif low.startswith(("</script", "</style")):
                skip = max(0, skip - 1)
            out.append(part)
        else:
            out.append(part if skip else typo_text(part))
    return "".join(out)


# ───────────────────────────── иконки ─────────────────────────────

ICONS = {
    "sprout": ("0 0 48 48", '<path d="M24 41V23"/><path d="M24 27c-8.500 0-13-5-13-13 8.500 0 13 4.500 13 13z"/><path d="M24 23c0-7.500 4.500-12 12-12 0 7.500-4.500 12-12 12z"/>'),
    "shield": ("0 0 48 48", '<path d="M24 6.500 38 11.500V22c0 9-5.800 16.500-14 20.500C15.800 38.500 10 31 10 22V11.500L24 6.500z"/><path d="m17 24 5 5 9.500-10.500"/>'),
    "heart": ("0 0 48 48", '<path d="M24 40.500S8.500 31 8.500 19.500A8 8 0 0 1 24 16.700 8 8 0 0 1 39.500 19.500C39.500 31 24 40.500 24 40.500z"/>'),
    "star": ("0 0 48 48", '<path d="m24 7 5.300 10.800 11.900 1.700-8.600 8.400 2 11.800L24 34.100 13.400 39.700l2-11.800-8.600-8.400 11.900-1.700L24 7z"/>'),
    "arrow": ("0 0 24 24", '<path d="M5 12h14M13 6l6 6-6 6"/>'),
    "phone": ("0 0 24 24", '<path d="M5 4h4l2 5-2.500 1.500a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>'),
    "mail": ("0 0 24 24", '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>'),
    "pin": ("0 0 24 24", '<path d="M12 21s-7-6.100-7-11a7 7 0 0 1 14 0c0 4.900-7 11-7 11z"/><circle cx="12" cy="10" r="2.500"/>'),
    "cart": ("0 0 24 24", '<circle cx="9" cy="20" r="1.300"/><circle cx="18" cy="20" r="1.300"/><path d="M3 4h2.500l2.200 11h10.300l2-8H6.500"/>'),
    "check": ("0 0 24 24", '<path d="m5 12.500 4.500 4.500L19 7.500"/>'),
}


def icon(name: str) -> str:
    vb, inner = ICONS[name]
    return f'<svg class="icon" viewBox="{vb}" aria-hidden="true" focusable="false">{inner}</svg>'


MARK_SVG = (
    '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" focusable="false">'
    '<circle cx="24" cy="24" r="22.200"/><path d="M24 37V15"/>'
    '<path d="M24 15c-2.600-2.200-2.600-5.600 0-8.400 2.600 2.800 2.600 6.200 0 8.400z"/>'
    '<path d="M24 22.500c-4.600.2-7.400-2.400-7.600-7 4.600-.2 7.400 2.400 7.600 7z"/><path d="M24 22.500c4.600.2 7.400-2.400 7.600-7-4.600-.2-7.400 2.400-7.600 7z"/>'
    '<path d="M24 30c-4.600.2-7.400-2.400-7.600-7 4.600-.2 7.400 2.400 7.600 7z"/><path d="M24 30c4.600.2 7.400-2.400 7.600-7-4.600-.2-7.400 2.400-7.600 7z"/>'
    '<path d="M14.500 37.500c2.400-2 4.800-2 7.200 0s4.800 2 7.200 0 4.800-2 7.200 0"/></svg>'
)


# ───────────────────────────── изображения ─────────────────────────────

def _webp_size(path: Path) -> tuple[int, int]:
    d = path.read_bytes()[:40]
    if d[:4] != b"RIFF" or d[8:12] != b"WEBP":
        raise ValueError(f"{path.name}: не WebP")
    fmt = d[12:16]
    if fmt == b"VP8 ":
        w, h = struct.unpack("<HH", d[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if fmt == b"VP8L":
        bits = int.from_bytes(d[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if fmt == b"VP8X":
        return int.from_bytes(d[24:27], "little") + 1, int.from_bytes(d[27:30], "little") + 1
    raise ValueError(f"{path.name}: неизвестный формат WebP")


IMAGES: dict[str, dict[int, int]] = {}


def scan_images() -> None:
    for p in sorted(IMG_DIR.glob("*.webp")):
        m = re.match(r"^(.+)-(\d+)\.webp$", p.name)
        if not m:
            continue
        w, h = _webp_size(p)
        IMAGES.setdefault(m.group(1), {})[w] = h


def img(root: str, name: str, alt: str, sizes: str = "100vw", cls: str = "", eager: bool = False) -> str:
    if name not in IMAGES:
        raise SystemExit(f"Нет изображения «{name}» в assets/img (ожидается {name}-<ширина>.webp)")
    variants = IMAGES[name]
    widths = sorted(variants)
    big = widths[-1]
    srcset = ", ".join(f"{root}assets/img/{name}-{w}.webp {w}w" for w in widths)
    attrs = [
        f'src="{root}assets/img/{name}-{big}.webp"',
        f'srcset="{srcset}"',
        f'sizes="{esc(sizes)}"',
        f'width="{big}"',
        f'height="{variants[big]}"',
        f'alt="{esc(alt)}"',
    ]
    if cls:
        attrs.append(f'class="{esc(cls)}"')
    attrs.append('decoding="async"')
    attrs.append('fetchpriority="high"' if eager else 'loading="lazy"')
    return f"<img {' '.join(attrs)}>"


# ───────────────────────────── данные ─────────────────────────────

SITE = load_json(CONTENT / "site.json")
NEWS = sorted(load_json(CONTENT / "news.json"), key=lambda n: n["date"], reverse=True)
FAQ = load_json(CONTENT / "faq.json")

CATEGORIES = {
    "Картофель": {
        "slug": "kartofel",
        "image": "potatoes",
        "product": "Картофель",
        "cta_title": "Картофель с целины",
        "cta_text": "Белый «Успех» и красный «Рэд леди» — без удобрений и пестицидов. Спросите о наличии.",
    },
    "Мёд и пчёлы": {
        "slug": "med",
        "image": "honey",
        "product": "Мёд",
        "cta_title": "Мёд с собственной пасеки",
        "cta_text": "Тёмный ароматный мёд, пчёлы породы «Карника». Предзаказ и наличие — по запросу.",
    },
    "Яйцо и птица": {
        "slug": "ptitsa",
        "image": "hens",
        "product": "Столовое яйцо",
        "cta_title": "Яйцо, птица и птенцы",
        "cta_text": "Птица на зерне и траве — без комбикормов, добавок и антибиотиков. Уточните наличие.",
    },
    "Земля и метод": {
        "slug": "zemlya",
        "image": "landscape",
        "product": "Другое",
        "cta_title": "Познакомьтесь с фермой",
        "cta_text": "Натуральное хозяйство в верховьях Волги: целина, зерно и трава, своя пасека.",
    },
    "Практика": {
        "slug": "praktika",
        "image": "hero",
        "product": "Другое",
        "cta_title": "Задайте вопрос фермеру",
        "cta_text": "Ответим по телефону и электронной почте — оставьте заявку на сайте.",
    },
}

PRODUCTS = ["Картофель", "Мёд", "Мясо птицы", "Столовое яйцо", "Суточные и подрощенные птенцы", "Другое"]


def load_articles() -> list[dict]:
    articles: list[dict] = []
    folder = CONTENT / "articles"
    if folder.exists():
        for f in sorted(folder.glob("*.json")):
            articles.extend(load_json(f))
    seen = set()
    for a in articles:
        if a["slug"] in seen:
            raise SystemExit(f"Повторяющийся slug: {a['slug']}")
        seen.add(a["slug"])
        if a["category"] not in CATEGORIES:
            raise SystemExit(f"{a['slug']}: неизвестная категория «{a['category']}»")
        a.setdefault("date", TODAY)
        a.setdefault("image", CATEGORIES[a["category"]]["image"])
        if a["image"] not in IMAGES:
            raise SystemExit(f"{a['slug']}: нет изображения «{a['image']}»")
        if len(a["description"]) > 175:
            WARNINGS.append(f"{a['slug']}: description {len(a['description'])} симв. (лучше ≤ 160)")
        if len(a["title"]) > 75:
            WARNINGS.append(f"{a['slug']}: title {len(a['title'])} симв. (лучше ≤ 70)")
    return articles


ARTICLES: list[dict] = []
BY_SLUG: dict[str, dict] = {}


# ───────────────────────────── вспомогательная разметка ─────────────────────────────

def expand_links(text: str, root: str) -> str:
    """[[slug|текст]] → ссылка; [[about|…]], [[news|…]], [[#contacts|…]] — служебные."""
    def rep(m: re.Match) -> str:
        target, label = m.group(1), m.group(2)
        if target in BY_SLUG:
            href = f"{root}articles/{target}/"
        elif target in ("about", "news", "articles"):
            href = f"{root}{target}/"
        elif target.startswith("#"):
            href = f"{root}index.html{target}"
        else:
            raise SystemExit(f"Неизвестная ссылка [[{target}|{label}]]")
        return f'<a href="{href}">{label}</a>'
    return re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", rep, text)


def render_blocks(blocks: list, root: str) -> str:
    out = []
    for b in blocks:
        if isinstance(b, str):
            out.append(f"<p>{expand_links(b, root)}</p>")
        elif "ul" in b:
            out.append("<ul>" + "".join(f"<li>{expand_links(i, root)}</li>" for i in b["ul"]) + "</ul>")
        elif "ol" in b:
            out.append("<ol>" + "".join(f"<li>{expand_links(i, root)}</li>" for i in b["ol"]) + "</ol>")
        else:
            raise SystemExit(f"Неизвестный блок: {b}")
    return "".join(out)


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", s)))


def article_words(a: dict) -> int:
    parts = [a["lead"], a.get("tip", ""), a.get("farm", "")]
    for s in a["sections"]:
        parts.append(s["heading"])
        for b in s["blocks"]:
            if isinstance(b, str):
                parts.append(b)
            else:
                parts.extend(b.get("ul", []) + b.get("ol", []))
    for f in a.get("faq", []):
        parts += [f["q"], f["a"]]
    return len(re.findall(r"\w+", strip_tags(" ".join(parts))))


def minutes(a: dict) -> int:
    return max(1, round(article_words(a) / 170))


def contact_how() -> str:
    bits = []
    if SITE.get("email"):
        bits.append(f'по адресу <a href="mailto:{esc(SITE["email"])}">{esc(SITE["email"])}</a>')
    if SITE.get("phone"):
        bits.append(f'по телефону <a href="tel:{esc(SITE["phone"])}">{esc(SITE.get("phone_display") or SITE["phone"])}</a>')
    return (" " + " или ".join(bits)) if bits else " через форму обратной связи на сайте"


def address_line() -> str:
    a = SITE["address"]
    return f'{a["region"]}, {a["district"]}, {a["locality"]}, {a["street"]}'


# ───────────────────────────── компоненты ─────────────────────────────

def brand_html(root: str) -> str:
    for fn in ("logo.svg", "logo.png", "logo.webp"):
        if (IMG_DIR / fn).exists():
            return f'<img class="brand__logo" src="{root}assets/img/{fn}" alt="{esc(SITE["name"])}" height="44">'
    return f'<span class="brand__mark" aria-hidden="true">{MARK_SVG}</span><span class="brand__word"><small>ферма</small>Рунская</span>'


def site_nav(root: str, home: str, current: str) -> str:
    items = [
        ("О ферме", f"{root}about/", "about"),
        ("Продукция", f"{home}#products", ""),
        ("Как мы растим", f"{home}#principles", ""),
        ("Хроника", f"{root}news/", "news"),
        ("Журнал", f"{root}articles/", "articles"),
        ("Контакты", f"{home}#contacts", ""),
    ]
    links = []
    for label, href, key in items:
        cur = ' aria-current="page"' if key and key == current else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    return "".join(links)


def header_html(root: str, home: str, variant: str, current: str) -> str:
    cls = "header header--overlay" if variant == "overlay" else "header header--solid"
    if SITE.get("phone"):
        cta = f'<a class="btn btn--small header__cta" href="tel:{esc(SITE["phone"])}">{icon("phone")}{esc(SITE.get("phone_display") or SITE["phone"])}</a>'
    else:
        cta = f'<a class="btn btn--small header__cta" href="{home}#contacts">Связаться</a>'
    return (
        f'<header class="{cls}" id="top"><div class="wrap header__inner">'
        f'<a class="brand" href="{root}index.html" aria-label="{esc(SITE["name"])} — на главную">{brand_html(root)}</a>'
        f'<nav class="nav" id="nav" aria-label="Основная навигация">{site_nav(root, home, current)}</nav>'
        f'{cta}'
        f'<button class="burger" type="button" aria-expanded="false" aria-controls="nav" aria-label="Открыть меню"><span></span><span></span><span></span></button>'
        f'</div></header>'
    )


def contact_items() -> str:
    a = SITE["address"]
    items = [
        f'<li>{icon("pin")}<div><span>Адрес фермы</span><p>{esc(a["region"])}, {esc(a["district"])},<br>{esc(a["locality"])}, {esc(a["street"])}</p>'
        f'<a class="link-arrow link-arrow--light" href="{esc(SITE["map_url"])}" target="_blank" rel="noopener noreferrer">Открыть на карте {icon("arrow")}</a></div></li>'
    ]
    if SITE.get("phone"):
        items.append(f'<li>{icon("phone")}<div><span>Телефон</span><p><a href="tel:{esc(SITE["phone"])}">{esc(SITE.get("phone_display") or SITE["phone"])}</a></p></div></li>')
    if SITE.get("email"):
        items.append(f'<li>{icon("mail")}<div><span>Электронная почта</span><p><a href="mailto:{esc(SITE["email"])}">{esc(SITE["email"])}</a></p></div></li>')
    items.append(f'<li>{icon("cart")}<div><span>Интернет-магазин</span><p>В разработке — заказы и вопросы принимаем напрямую.</p></div></li>')
    return "".join(items)


def footer_html(root: str, home: str) -> str:
    a = SITE["address"]
    top = [x for x in ARTICLES if x.get("featured")][:4] or ARTICLES[:4]
    journal = "".join(f'<li><a href="{root}articles/{x["slug"]}/">{esc(x["title"])}</a></li>' for x in top)
    extra = ""
    if SITE.get("phone"):
        extra += f'<p><a href="tel:{esc(SITE["phone"])}">{esc(SITE.get("phone_display") or SITE["phone"])}</a></p>'
    if SITE.get("email"):
        extra += f'<p><a href="mailto:{esc(SITE["email"])}">{esc(SITE["email"])}</a></p>'
    year_from = SITE.get("since", 2022)
    return f"""<footer class="footer">
  <div class="wrap footer__grid">
    <div class="footer__brand">
      <a class="brand brand--light" href="{root}index.html" aria-label="{esc(SITE["name"])} — на главную">{brand_html(root)}</a>
      <p>{esc(SITE["tagline"])}. Едим сами и кормим наших детей тем, что выращиваем.</p>
    </div>
    <nav aria-label="Разделы сайта"><h4>Разделы</h4><ul>
      <li><a href="{root}about/">О ферме</a></li>
      <li><a href="{home}#products">Продукция</a></li>
      <li><a href="{home}#principles">Как мы растим</a></li>
      <li><a href="{root}news/">Хроника</a></li>
      <li><a href="{root}articles/">Журнал</a></li>
      <li><a href="{home}#contacts">Контакты</a></li>
    </ul></nav>
    <nav aria-label="Из журнала"><h4>Из журнала</h4><ul>{journal}</ul></nav>
    <div><h4>Контакты</h4><address>
      <p>{esc(a["region"])}, {esc(a["district"])}, {esc(a["locality"])}, {esc(a["street"])}</p>{extra}
      <p><a href="{esc(SITE["map_url"])}" target="_blank" rel="noopener noreferrer">Открыть на карте</a></p>
    </address></div>
  </div>
  <div class="wrap footer__bottom">
    <p>© {year_from}–<span data-year>{TODAY[:4]}</span> {esc(SITE["name"])}. Сайт не использует cookies и трекеры.</p>
    <p><a href="{root}privacy/">Политика конфиденциальности</a> · <a href="{root}sitemap.xml">Карта сайта</a></p>
    <p class="footer__legal">Информация на сайте носит справочный характер и не является публичной офертой. Наличие и условия получения продукции уточняйте у фермы.</p>
  </div>
</footer>"""


def dock_html(home: str) -> str:
    return (
        f'<div class="dock" data-dock aria-hidden="true"><span>Узнать о наличии продукции</span>'
        f'<a class="btn btn--honey btn--small" href="{home}#contacts" tabindex="-1">Связаться</a></div>'
    )


def org_jsonld() -> dict:
    a = SITE["address"]
    data = {
        "@type": "LocalBusiness",
        "@id": SITE_BASE + "#farm",
        "name": SITE["name"],
        "url": SITE_BASE,
        "image": SITE_BASE + "assets/img/og-cover.jpg",
        "logo": SITE_BASE + "assets/img/icon-512.png",
        "description": SITE["description"],
        "slogan": "Едим сами и кормим наших детей тем, что выращиваем",
        "foundingDate": str(SITE.get("since", 2022)),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": a["street"],
            "addressLocality": a["locality"],
            "addressRegion": a["region"],
            "postalCode": a["postal"],
            "addressCountry": a["country"],
        },
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Продукция фермы",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Product", "name": n}}
                for n in ["Картофель", "Мёд", "Мясо птицы", "Столовое яйцо", "Суточные и подрощенные птенцы"]
            ],
        },
    }
    if SITE.get("phone"):
        data["telephone"] = SITE["phone"]
    if SITE.get("email"):
        data["email"] = SITE["email"]
    return data


def breadcrumb_jsonld(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(items)
        ],
    }


def layout(*, root: str, path: str, title: str, description: str, body: str,
           header: str = "solid", current: str = "", og_image: str = "assets/img/og-cover.jpg",
           og_alt: str = "", og_type: str = "website", jsonld: list | None = None,
           preload_hero: bool = False, noindex: bool = False, base: bool = False,
           published: str = "", modified: str = "") -> str:
    home = "" if path == "" else f"{root}index.html"
    full_title = title if path == "" else f"{title} — {SITE['name']}"
    canonical = SITE_BASE + path
    og_img_url = SITE_BASE + og_image
    og_alt = og_alt or f"{SITE['name']} — {SITE['tagline']}"
    h = ['<!doctype html>', '<html lang="ru">', "<head>", '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">']
    if base:
        h.append(f'<base href="{SITE_BASE}">')
    h.append(f"<title>{esc(full_title)}</title>")
    h.append(f'<meta name="description" content="{esc(description)}">')
    h.append('<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">')
    if not noindex:
        h.append(f'<link rel="canonical" href="{canonical}">')
    h.append('<meta name="theme-color" content="#13291c">')
    h += [
        f'<meta property="og:site_name" content="{esc(SITE["name"])}">',
        '<meta property="og:locale" content="ru_RU">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(full_title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{og_img_url}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{esc(og_alt)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(full_title)}">',
        f'<meta name="twitter:description" content="{esc(description)}">',
        f'<meta name="twitter:image" content="{og_img_url}">',
        f'<meta name="twitter:image:alt" content="{esc(og_alt)}">',
    ]
    if published:
        h.append(f'<meta property="article:published_time" content="{published}">')
        h.append(f'<meta property="article:modified_time" content="{modified or published}">')
    h += [
        f'<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">',
        f'<link rel="icon" href="{root}assets/img/favicon-32.png" type="image/png" sizes="32x32">',
        f'<link rel="apple-touch-icon" href="{root}assets/img/apple-touch-icon.png">',
        f'<link rel="manifest" href="{root}manifest.webmanifest">',
        f'<link rel="preload" href="{root}assets/fonts/alegreya-cyrillic-wght-normal.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="preload" href="{root}assets/fonts/manrope-cyrillic-wght-normal.woff2" as="font" type="font/woff2" crossorigin>',
    ]
    if preload_hero and "hero" in IMAGES:
        ws = sorted(IMAGES["hero"])
        srcset = ", ".join(f"{root}assets/img/hero-{w}.webp {w}w" for w in ws)
        h.append(f'<link rel="preload" as="image" href="{root}assets/img/hero-{ws[-1]}.webp" imagesrcset="{srcset}" imagesizes="100vw" fetchpriority="high">')
    h.append(f'<link rel="stylesheet" href="{root}assets/css/main.css?v={asset_v("assets/css/main.css")}">')
    h.append("<script>document.documentElement.classList.add('js')</script>")
    if jsonld:
        graph = json.dumps({"@context": "https://schema.org", "@graph": jsonld}, ensure_ascii=False, separators=(",", ":"))
        h.append(f'<script type="application/ld+json">{graph}</script>')
    h.append("</head>")
    body_cls = "page-home" if path == "" else "page-inner"
    announce = f'<div class="announce"><span class="announce__dot"></span>{esc(SITE["tagline"])} · Тверская область</div>'
    page = (
        "\n".join(h)
        + f'\n<body class="{body_cls}">\n<a class="skip-link" href="#main">К содержимому</a>\n{announce}\n'
        + header_html(root, home, header, current)
        + f'\n<main id="main">\n{body}\n</main>\n'
        + footer_html(root, home) + "\n" + dock_html(home)
        + f'\n<script src="{root}assets/js/main.js?v={asset_v("assets/js/main.js")}" defer></script>\n</body>\n</html>\n'
    )
    # типографика — только для тела страницы
    head_end = page.index("</head>")
    return page[:head_end] + typo_html(page[head_end:])


# ───────────────────────────── токены шаблонов ─────────────────────────────

def render_tokens(text: str, *, root: str, home: str, extra: dict | None = None) -> str:
    ctx = {
        "root": root,
        "home": home,
        "map_url": SITE["map_url"],
        "today_ru": ru_date(TODAY),
        "address_line": address_line(),
        "contact_how": contact_how(),
        "contact_items": contact_items(),
        "form_attrs": (f' data-email="{esc(SITE["email"])}"' if SITE.get("email") else "") + (f' data-phone="{esc(SITE["phone"])}"' if SITE.get("phone") else ""),
        "product_options": '<option value="">Выберите…</option>' + "".join(f"<option>{esc(p)}</option>" for p in PRODUCTS),
    }
    ctx.update(extra or {})

    def img_token(m: re.Match) -> str:
        parts = [p.strip() for p in m.group(1).split("|")]
        name, alt = parts[0], parts[1]
        sizes = parts[2] if len(parts) > 2 and parts[2] else "100vw"
        cls = parts[3] if len(parts) > 3 else ""
        eager = len(parts) > 4 and parts[4] == "eager"
        return img(root, name, alt, sizes, cls, eager)

    text = re.sub(r"\{\{img:([^}]+)\}\}", img_token, text)
    text = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: icon(m.group(1)), text)
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", str(value))
    leftover = re.findall(r"\{\{[^}]+\}\}", text)
    if leftover:
        raise SystemExit(f"Неподставленные токены: {leftover}")
    return text


def template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


# ───────────────────────────── карточки ─────────────────────────────

def news_card(n: dict, root: str) -> str:
    href = f"{root}news/#{n['id']}"
    return (
        f'<article class="card card--news reveal">'
        f'<a class="card__media" href="{href}" tabindex="-1" aria-hidden="true">{img(root, n["image"], "", "(min-width: 1100px) 24vw, (min-width: 640px) 46vw, 92vw")}</a>'
        f'<div class="card__body"><p class="card__meta"><time datetime="{n["date"]}">{ru_date(n["date"])}</time></p>'
        f'<h3 class="card__title"><a href="{href}">{esc(n["title"])}</a></h3>'
        f'<p class="card__text">{esc(n["excerpt"])}</p></div></article>'
    )


def article_card(a: dict, root: str, delay: str = "") -> str:
    href = f"{root}articles/{a['slug']}/"
    search = esc(f"{a['title']} {a['category']} {a['description']} {a.get('query', '')}".lower())
    style = f' style="--d:{delay}"' if delay else ""
    return (
        f'<article class="card card--article reveal" data-category="{esc(a["category"])}" data-search="{search}"{style}>'
        f'<a class="card__media" href="{href}" tabindex="-1" aria-hidden="true">{img(root, a["image"], "", "(min-width: 1100px) 30vw, (min-width: 640px) 46vw, 92vw")}</a>'
        f'<div class="card__body"><p class="card__meta"><span class="tag">{esc(a["category"])}</span><span>{minutes(a)} мин чтения</span></p>'
        f'<h3 class="card__title"><a href="{href}">{esc(a["title"])}</a></h3>'
        f'<p class="card__text">{esc(a["description"])}</p></div></article>'
    )


def faq_html() -> str:
    return "".join(
        f'<details class="faq-item"><summary>{esc(f["q"])}</summary><div class="faq-item__a"><p>{f["a"]}</p></div></details>'
        for f in FAQ
    )


def ticker_html() -> str:
    items = ["Картофель", "Мёд", "Яйцо", "Мясо птицы", "Индюки и гуси", "Суточные птенцы", "Собственная пасека", "Целинные земли", "Верховья Волги"]
    one = "".join(f'<span class="ticker__item">{esc(t)}<i></i></span>' for t in items)
    return one + one


# ───────────────────────────── страницы ─────────────────────────────

def page_home() -> str:
    root, home = "", ""
    featured = [a for a in ARTICLES if a.get("featured")][:6] or ARTICLES[:6]
    extra = {
        "ticker": ticker_html(),
        "news_cards": "".join(news_card(n, root).replace('class="card card--news reveal"', f'class="card card--news reveal" style="--d:{i * 0.07:.2f}s"') for i, n in enumerate(NEWS[:4])),
        "journal_cards": "".join(article_card(a, root, f"{i % 3 * 0.08:.2f}s") for i, a in enumerate(featured)),
        "faq_items": faq_html(),
    }
    body = render_tokens(template("home.html"), root=root, home=home, extra=extra)
    faq_ld = {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": strip_tags(f["a"])}}
            for f in FAQ
        ],
    }
    ld = [
        org_jsonld(),
        {"@type": "WebSite", "@id": SITE_BASE + "#website", "url": SITE_BASE, "name": SITE["name"], "inLanguage": "ru-RU", "publisher": {"@id": SITE_BASE + "#farm"}},
        faq_ld,
    ]
    return layout(
        root=root, path="", header="overlay",
        title="Ферма «Рунская» — картофель, мёд, яйцо и птица из верховьев Волги",
        description="Натуральная ферма в верховьях Волги, Тверская область: картофель с целины без удобрений, мёд с собственной пасеки, яйцо и мясо птицы на зерне и траве.",
        body=body, jsonld=ld, preload_hero=True,
        og_alt="Ферма «Рунская»: поле, лес и река в верховьях Волги на рассвете",
    )


def page_about() -> str:
    root, home = "../", "../index.html"
    body = render_tokens(template("about.html"), root=root, home=home)
    ld = [breadcrumb_jsonld([("Главная", SITE_BASE), ("О ферме", SITE_BASE + "about/")]),
          {"@type": "AboutPage", "url": SITE_BASE + "about/", "name": "О ферме «Рунская»", "inLanguage": "ru-RU", "about": {"@id": SITE_BASE + "#farm"}}]
    return layout(
        root=root, path="about/", current="about",
        title="О ферме «Рунская»: натуральное хозяйство у истоков Волги",
        description="История и метод фермы «Рунская»: целинные земли без удобрений, агротехнологии 20-х годов XX века, птица на зерне и траве, собственные семена и пасека.",
        body=body, jsonld=ld,
    )


def page_privacy() -> str:
    root, home = "../", "../index.html"
    body = render_tokens(template("privacy.html"), root=root, home=home)
    return layout(root=root, path="privacy/", title="Политика конфиденциальности",
                  description="Как ферма «Рунская» обрабатывает персональные данные, которые вы оставляете в форме обратной связи.",
                  body=body, noindex=False)


def page_404() -> str:
    body = render_tokens(template("404.html"), root="", home="")
    return layout(root="", path="404.html", title="Страница не найдена", description="Страница не найдена.",
                  body=body, noindex=True, base=True)


def page_news() -> str:
    root, home = "../", "../index.html"
    items = []
    for n in NEWS:
        blocks = render_blocks(n["body"], root)
        items.append(
            f'<li class="tl-item reveal" id="{n["id"]}">'
            f'<div class="tl-date"><time datetime="{n["date"]}"><b>{int(n["date"][8:]):d}</b><span>{MONTHS[int(n["date"][5:7]) - 1]} {n["date"][:4]}</span></time></div>'
            f'<article class="tl-card"><div class="tl-card__media">{img(root, n["image"], n["alt"], "(min-width: 900px) 34vw, 92vw")}</div>'
            f'<div class="tl-card__body"><h2>{esc(n["title"])}</h2><div class="prose">{blocks}</div></div></article></li>'
        )
    body = f"""<section class="page-hero page-hero--plain">
  <div class="wrap page-hero__inner">
    <nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="{root}index.html">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Хроника</span></nav>
    <p class="eyebrow"><span class="eyebrow__line"></span>Сезон 2022</p>
    <h1>Хроника <em>хозяйства</em></h1>
    <p class="page-hero__lead">Записи из жизни фермы «Рунская»: от закупки инкубационного яйца и первых гектаров до первого мёда, картофеля и столового яйца.</p>
  </div>
</section>
<section class="section section--tight">
  <div class="wrap"><ol class="timeline">{''.join(items)}</ol>
  <aside class="cta-inline reveal"><p>Хотите узнать, что сейчас есть в наличии?</p><a class="btn btn--dark" href="{home}#contacts">Связаться с нами {icon("arrow")}</a></aside></div>
</section>"""
    ld = [breadcrumb_jsonld([("Главная", SITE_BASE), ("Хроника", SITE_BASE + "news/")]),
          {"@type": "CollectionPage", "url": SITE_BASE + "news/", "name": "Хроника хозяйства", "inLanguage": "ru-RU"}]
    return layout(
        root=root, path="news/", current="news",
        title="Хроника хозяйства: сезон 2022 на ферме «Рунская»",
        description="Новости фермы «Рунская»: инкубатор и птенцы, посевная, пасека «Карника», мёд, картофель «Успех» и «Рэд леди», первые продажи яйца и мяса птицы.",
        body=body, jsonld=ld,
    )


def page_library() -> str:
    root, home = "../", "../index.html"
    cats = [c for c in CATEGORIES if any(a["category"] == c for a in ARTICLES)]
    chips = '<button class="filter is-active" type="button" data-filter="all">Все темы</button>' + "".join(
        f'<button class="filter" type="button" data-filter="{esc(c)}">{esc(c)}</button>' for c in cats
    )
    cards = "".join(article_card(a, root, f"{i % 3 * 0.06:.2f}s") for i, a in enumerate(ARTICLES))
    body = f"""<section class="page-hero page-hero--plain">
  <div class="wrap page-hero__inner">
    <nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="{root}index.html">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Журнал</span></nav>
    <p class="eyebrow"><span class="eyebrow__line"></span>Журнал фермы</p>
    <h1>Про картофель, мёд, птицу <em>и землю</em></h1>
    <p class="page-hero__lead">Практические статьи: как хранить, выбирать и готовить натуральные продукты — и как всё это выращивается на нашей ферме.</p>
    <div class="library-stats"><span><b>{len(ARTICLES)}</b> статей</span><span><b>{len(cats)}</b> тематических разделов</span><span>Обновлено {ru_date_short(TODAY)}</span></div>
  </div>
</section>
<section class="section section--tight library">
  <div class="wrap">
    <div class="library__toolbar">
      <div class="filters" role="group" aria-label="Фильтр по темам">{chips}</div>
      <label class="search"><span class="visually-hidden">Поиск по статьям</span><input id="article-search" type="search" placeholder="Поиск: например, «мёд» или «картофель»" autocomplete="off"></label>
    </div>
    <p class="library__count" aria-live="polite"><span data-count>{len(ARTICLES)}</span> из {len(ARTICLES)} статей</p>
    <div class="card-grid card-grid--3" id="article-grid">{cards}</div>
    <p class="library__empty" hidden>Ничего не найдено. Попробуйте другое слово или сбросьте фильтр.</p>
  </div>
</section>"""
    ld = [breadcrumb_jsonld([("Главная", SITE_BASE), ("Журнал", SITE_BASE + "articles/")]),
          {"@type": "CollectionPage", "url": SITE_BASE + "articles/", "name": "Журнал фермы «Рунская»", "inLanguage": "ru-RU",
           "mainEntity": {"@type": "ItemList", "itemListElement": [
               {"@type": "ListItem", "position": i + 1, "url": f"{SITE_BASE}articles/{a['slug']}/", "name": a["title"]} for i, a in enumerate(ARTICLES)]}}]
    return layout(
        root=root, path="articles/", current="articles",
        title="Журнал фермы: статьи про картофель, мёд, яйцо и птицу",
        description=f"{len(ARTICLES)} практических статей фермы «Рунская»: хранение картофеля и мёда, свежесть яиц, породы птицы, пчёлы «Карника», агротехнологии 1920-х.",
        body=body, jsonld=ld,
    )


def related_for(a: dict, limit: int = 3) -> list[dict]:
    if a.get("related"):
        return [BY_SLUG[s] for s in a["related"] if s in BY_SLUG][:limit]
    same = [x for x in ARTICLES if x["category"] == a["category"] and x["slug"] != a["slug"]]
    rest = [x for x in ARTICLES if x["category"] != a["category"]]
    return (same + rest)[:limit]


def page_article(a: dict) -> str:
    root, home = "../../", "../../index.html"
    cat = CATEGORIES[a["category"]]
    product = a.get("product", cat["product"])
    mins = minutes(a)
    toc = "".join(f'<a href="#s{i + 1}">{esc(s["heading"])}</a>' for i, s in enumerate(a["sections"]))
    sections = "".join(
        f'<section class="prose-section" id="s{i + 1}"><h2>{esc(s["heading"])}</h2>{render_blocks(s["blocks"], root)}</section>'
        for i, s in enumerate(a["sections"])
    )
    tip = ""
    if a.get("tip"):
        tip = f'<aside class="tip"><span class="tip__label">Практический совет</span><p>{expand_links(a["tip"], root)}</p></aside>'
    farm = ""
    if a.get("farm"):
        farm = f'<aside class="farm-note"><span class="farm-note__label">Из практики фермы «Рунская»</span><p>{expand_links(a["farm"], root)}</p></aside>'
    faq = ""
    if a.get("faq"):
        faq = '<section class="article-faq"><h2>Частые вопросы</h2>' + "".join(
            f'<details class="faq-item"><summary>{esc(f["q"])}</summary><div class="faq-item__a"><p>{expand_links(f["a"], root)}</p></div></details>'
            for f in a["faq"]) + "</section>"
    related = "".join(article_card(x, root) for x in related_for(a))
    from urllib.parse import quote
    cta_href = f'{home}?product={quote(product)}#contacts'
    url = f"{SITE_BASE}articles/{a['slug']}/"

    body = f"""<article class="article-page">
  <header class="article-head">
    <div class="wrap wrap--article">
      <nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="{root}index.html">Главная</a><span aria-hidden="true">/</span><a href="{root}articles/">Журнал</a><span aria-hidden="true">/</span><span aria-current="page">{esc(a["category"])}</span></nav>
      <p class="eyebrow"><span class="eyebrow__line"></span>{esc(a["category"])} · {mins} мин чтения</p>
      <h1>{esc(a["title"])}</h1>
      <p class="article-lead">{expand_links(a["lead"], root)}</p>
      <p class="article-meta">Обновлено {ru_date(a["date"])} · Материал справочный</p>
    </div>
  </header>
  <div class="wrap wrap--article"><figure class="article-cover">{img(root, a["image"], a.get("alt", a["title"]), "(min-width: 1100px) 1100px, 94vw", "", True)}</figure></div>
  <div class="wrap wrap--article article-layout">
    <div class="prose article-body">
      <nav class="toc toc--inline" aria-label="Содержание статьи"><b>В статье</b>{toc}</nav>
      {sections}
      {tip}
      {farm}
      {faq}
    </div>
    <aside class="article-aside">
      <nav class="toc" aria-label="Содержание статьи"><b>В статье</b>{toc}</nav>
      <div class="aside-card">
        <span class="aside-card__label">С нашей фермы</span>
        <h2>{esc(cat["cta_title"])}</h2>
        <p>{esc(cat["cta_text"])}</p>
        <a class="btn btn--honey btn--block" href="{cta_href}">Узнать о наличии {icon("arrow")}</a>
      </div>
    </aside>
  </div>
  <section class="section section--sand related"><div class="wrap">
    <header class="section-head"><div><p class="eyebrow"><span class="eyebrow__line"></span>Читайте также</p><h2>Ещё из <em>журнала</em></h2></div>
    <a class="link-arrow" href="{root}articles/">Все статьи {icon("arrow")}</a></header>
    <div class="card-grid card-grid--3">{related}</div></div></section>
</article>"""

    ld = [
        {"@type": "Article", "headline": a["title"], "description": a["description"], "inLanguage": "ru-RU",
         "datePublished": a["date"], "dateModified": a["date"], "mainEntityOfPage": url,
         "image": f"{SITE_BASE}assets/img/{a['image']}-{max(IMAGES[a['image']])}.webp",
         "articleSection": a["category"], "keywords": a.get("query", ""),
         "author": {"@type": "Organization", "name": SITE["name"]},
         "publisher": {"@id": SITE_BASE + "#farm"}},
        breadcrumb_jsonld([("Главная", SITE_BASE), ("Журнал", SITE_BASE + "articles/"), (a["title"], url)]),
    ]
    if a.get("faq"):
        ld.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": strip_tags(f["a"])}} for f in a["faq"]]})
    return layout(
        root=root, path=f"articles/{a['slug']}/", current="articles",
        title=a["title"], description=a["description"], body=body, jsonld=ld,
        og_type="article", published=a["date"], modified=a["date"],
        og_alt=a.get("alt", a["title"]),
    )


# ───────────────────────────── служебные файлы ─────────────────────────────

def build_sitemap() -> None:
    urls = [("", TODAY), ("about/", TODAY), ("news/", NEWS[0]["date"] if NEWS else TODAY), ("articles/", TODAY), ("privacy/", TODAY)]
    urls += [(f"articles/{a['slug']}/", a["date"]) for a in ARTICLES]
    rows = "".join(f"  <url><loc>{SITE_BASE}{p}</loc><lastmod>{d}</lastmod></url>\n" for p, d in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /send.php\n\nSitemap: {SITE_BASE}sitemap.xml\n")


def build_manifest() -> None:
    data = {
        "name": SITE["name"], "short_name": SITE["short_name"], "description": SITE["tagline"],
        "lang": "ru", "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#f6f1e3", "theme_color": "#13291c",
        "icons": [
            {"src": "assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    write("manifest.webmanifest", json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def build_seo_plan() -> None:
    rows = "\n".join(
        f"| {i + 1} | {a.get('query', '—')} | {a['title']} | {a['category']} | [{a['slug']}]({SITE_BASE}articles/{a['slug']}/) |"
        for i, a in enumerate(ARTICLES)
    )
    text = f"""# SEO-контент-план: журнал фермы «Рунская»

Статей: **{len(ARTICLES)}**. Материалы ориентированы на информационные запросы вокруг продукции фермы — картофеля, мёда, яйца, птицы и натурального земледелия — и ведут читателя к заявке на сайте.
Частотность и конкуренция запросов здесь **не заявлены**: перед масштабированием кластеров проверьте их в Яндекс Wordstat, Яндекс Вебмастере и Google Search Console.

| № | Основной запрос | Заголовок | Раздел | URL |
|---:|---|---|---|---|
{rows}

## Перед запуском

- Проверьте факты о ферме (сорта, породы, сроки, наличие) — тексты опираются на то, что сказано на fermaruna.ru.
- Общие сведения (хранение, свежесть, сроки инкубации и т. п.) носят справочный характер. Они не заменяют рекомендации специалистов.
- Добавьте телефон и e-mail в `content/site.json`, замените иллюстрации реальными фотографиями и пересоберите сайт: `python3 scripts/build.py`.
- Зарегистрируйте сайт в Яндекс Вебмастере и Google Search Console, отправьте `sitemap.xml`.
- Для боевого домена задайте канонический адрес: `SITE_BASE_URL=https://fermaruna.ru python3 scripts/build.py`.
- Не публикуйте непроверенные отзывы, цены и обещания: на сайте их нет намеренно.
"""
    write("SEO_PLAN.md", text)


# ───────────────────────────── main ─────────────────────────────

def main() -> None:
    global ARTICLES, BY_SLUG
    scan_images()
    ARTICLES = load_articles()
    BY_SLUG = {a["slug"]: a for a in ARTICLES}

    write("index.html", page_home())
    write("about/index.html", page_about())
    write("news/index.html", page_news())
    write("articles/index.html", page_library())
    for a in ARTICLES:
        write(f"articles/{a['slug']}/index.html", page_article(a))
    write("privacy/index.html", page_privacy())
    write("404.html", page_404())
    build_sitemap()
    build_manifest()
    build_seo_plan()

    print(f"Готово: {len(ARTICLES)} статей, {len(NEWS)} записей хроники. Канонический адрес: {SITE_BASE}")
    if not SITE.get("phone") and not SITE.get("email"):
        WARNINGS.append("В content/site.json не заполнены phone/email — на сайте показывается только адрес.")
    if not (ROOT / "assets/img/og-cover.jpg").exists():
        WARNINGS.append("Нет assets/img/og-cover.jpg (обложка для соцсетей 1200×630).")
    for w in WARNINGS:
        print("  ⚠", w)


if __name__ == "__main__":
    sys.exit(main())
