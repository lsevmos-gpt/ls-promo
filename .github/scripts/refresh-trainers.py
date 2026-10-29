#!/usr/bin/env python3
"""Render the sourced trainer directory, profiles and club rosters in the static site.

Run from any directory. Only trainer markup and its dedicated asset references change;
the remaining page source is retained verbatim.
"""
from pathlib import Path
from html import escape
import hashlib
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'new-site'
DATA = json.loads((SITE / 'data/trainers.json').read_text())
CONTENT_PATH = SITE / 'assets/content.js'
content_source = CONTENT_PATH.read_text()
prefix = 'window.LS_DATA = '
assert content_source.startswith(prefix)
CONTENT = json.loads(content_source[len(prefix):].strip().removesuffix(';'))
CLUBS = {c['id']: c for c in CONTENT['clubs']}
TRAINERS = {t['id']: t for t in DATA['trainers']}
ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'
UP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5M5 5h14v14"/></svg>'
e = escape


def image(src, alt, eager=False, **dimensions):
    attrs = ''.join(f' {k}="{v}"' for k, v in dimensions.items())
    return (f'<img src="{e(src)}" alt="{e(alt)}" loading="{"eager" if eager else "lazy"}" decoding="async"'
            + (' fetchpriority="high"' if eager else '') + attrs + '>')


def card(t):
    names = ' · '.join(CLUBS[c]['street'] for c in t['clubs'])
    return (f'<a class="trainer-card" href="/trainers/{t["id"]}/" data-trainer-clubs="{" ".join(t["clubs"])}">'
            f'<div class="trainer-image">{image(t["image"], t["name"], width=t["portrait"]["width"], height=t["portrait"]["height"])}<span class="trainer-arrow">{UP}</span></div>'
            f'<div class="trainer-caption"><h3>{e(t["name"])}</h3><p>{e(t["speciality"])}</p>'
            f'<p class="trainer-card-clubs"><span class="trainer-club-label">Клуб{ "ы" if len(t["clubs"]) > 1 else ""}</span>{e(names)}</p></div></a>')


def replace_section(text, marker, replacement):
    # Sections do not contain nested <section> elements in these static templates.
    pattern = rf'<section\b[^>]*{marker}[^>]*>[\s\S]*?</section>'
    text, n = re.subn(pattern, lambda _: replacement, text, count=1)
    if n != 1:
        raise ValueError(f'Expected one section: {marker}')
    return text


def asset_links(text):
    for kind, filename in [('style', 'trainers.css'), ('script', 'trainers.js')]:
        digest = hashlib.sha256((SITE / 'assets' / filename).read_bytes()).hexdigest()[:12]
        text = re.sub(rf'<(?:link|script)\b[^>]*(?:href|src)="/assets/{re.escape(filename)}(?:\?[^" ]*)?"[^>]*>(?:</script>)?', '', text)
        tag = (f'<link rel="stylesheet" href="/assets/{filename}?v={digest}">' if kind == 'style'
               else f'<script src="/assets/{filename}?v={digest}" defer></script>')
        text = text.replace('</head>', tag + '</head>', 1)
    return text


def save(path, text):
    path.write_text(asset_links(text))


def club_section(cid):
    roster = next(c['trainers'] for c in DATA['club_sources'] if c['id'] == cid)
    cards = ''.join(card(TRAINERS[tid]) for tid in roster)
    return (f'<section class="section club-team-section" id="trainers"><div class="container">'
            f'<div class="section-head"><div><p class="eyebrow">КОМАНДА КЛУБА</p><span class="accent-line" aria-hidden="true"></span>'
            f'<h2>ТВОИ ТРЕНЕРЫ.</h2></div><p class="section-intro">Тренируют в клубе на {e(CLUBS[cid]["street"])}. '
            'Откройте страницу тренера, чтобы узнать об опыте, направлениях и достижениях.</p></div>'
            f'<div class="trainer-grid club-trainer-grid">{cards}</div>'
            f'<div class="section-footer"><p>Подобрать тренера и время занятия поможет администратор клуба.</p>'
            f'<a class="text-link" href="tel:{CLUBS[cid]["tel"]}">{e(CLUBS[cid]["phone"])} {ARROW}</a></div></div></section>')


def directory_section():
    filters = f'<button type="button" class="team-club-filter active" data-team-club="all" aria-pressed="true">Все клубы <span>{len(TRAINERS)}</span></button>'
    for source in DATA['club_sources']:
        cid = source['id']
        filters += (f'<button type="button" class="team-club-filter" data-team-club="{cid}" aria-pressed="false">'
                    f'{e(CLUBS[cid]["street"])} <span>{len(source["trainers"])}</span></button>')
    return ('<section class="section team-page"><div class="container"><div class="section-head"><div>'
            '<p class="eyebrow">КОМАНДА / ЛИНИЯ СПОРТА</p><span class="accent-line" aria-hidden="true"></span>'
            '<h1 class="page-heading">С ПОДДЕРЖКОЙ<br>ПРОЩЕ.</h1></div>'
            '<p class="section-intro">Выберите свой клуб и познакомьтесь с его командой. Опыт, направления работы и фотографии — на странице каждого тренера.</p></div>'
            f'<div class="team-club-filters" role="group" aria-label="Выбрать клуб тренера">{filters}</div>'
            '<label class="trainer-search" for="team-search"><span>Найти тренера по имени или направлению</span>'
            '<input id="team-search" type="search" placeholder="Имя или направление" autocomplete="off" aria-controls="team-results"></label>'
            f'<p class="team-result-count" id="team-result-count" role="status" aria-live="polite">Найдено: {len(TRAINERS)}</p>'
            f'<div class="trainer-grid all-trainers" id="team-results">{"".join(card(t) for t in TRAINERS.values())}</div>'
            '<div class="team-empty" hidden><p>По вашему запросу тренеров не найдено.</p>'
            '<button type="button" class="text-link" data-reset-team>Сбросить фильтры ' + ARROW + '</button></div></div></section>')


def photo_tile(t, i, photo):
    label = f'{t["name"]} — фото {i + 1}'
    return (f'<a class="trainer-photo-tile" href="{photo["path"]}" data-trainer-photo="{i}" aria-label="Открыть фото {i + 1}: {e(t["name"])}">'
            f'{image(photo["path"], label, width=photo["width"], height=photo["height"])}'
            f'<span>{i + 1:02d} {UP}</span></a>')


def profile(t):
    clubs = ''
    for cid in t['clubs']:
        c = CLUBS[cid]
        clubs += (f'<div class="profile-club"><a class="profile-club-name" href="/clubs/{cid}/#trainers">{e(c["street"])} {UP}</a>'
                  f'<a class="profile-club-phone" href="tel:{c["tel"]}" aria-label="Запись к тренеру: клуб {e(c["street"])}, {e(c["phone"])}">'
                  f'Запись: {e(c["phone"])}</a></div>')
    gallery = t['gallery']
    tiles = '<div class="trainer-photo-grid">' + ''.join(photo_tile(t, i, p) for i, p in enumerate(gallery[:4])) + '</div>'
    if len(gallery) > 4:
        rest = ''.join(photo_tile(t, i, p) for i, p in enumerate(gallery[4:], 4))
        tiles += f'<details class="trainer-more-photos"><summary>Все фотографии <span>+{len(gallery) - 4}</span></summary><div class="trainer-photo-grid">{rest}</div></details>'
    photos = (f'<section class="section trainer-photos-section" aria-labelledby="trainer-photos-title"><div class="container">'
              '<div class="section-head"><div><p class="eyebrow">ЛИЧНЫЕ ФОТОГРАФИИ И ДОСТИЖЕНИЯ</p><span class="accent-line" aria-hidden="true"></span>'
              '<h2 id="trainer-photos-title">В КАДРЕ.</h2></div><p class="section-intro">Тренировки, соревнования и квалификация. Нажмите на фото, чтобы рассмотреть его полностью.</p></div>'
              f'{tiles}</div></section>') if gallery else ''
    return (f'<div class="container breadcrumb"><a href="/">Главная</a><span>/</span><a href="/trainers/">Команда</a><span>/</span><span>{e(t["name"])}</span></div>'
            '<section class="section trainer-profile trainer-profile-complete container">'
            f'<figure>{image(t["image"], t["name"], True, width=t["portrait"]["width"], height=t["portrait"]["height"])}</figure><div class="trainer-profile-heading"><p class="eyebrow">КОМАНДА / ПЕРСОНАЛЬНЫЙ ТРЕНЕР</p>'
            f'<span class="accent-line" aria-hidden="true"></span><h1>{e(t["name"].upper())}</h1>'
            f'<p class="profile-speciality">{e(t["speciality"])}</p><div class="profile-availability"><h2>Тренирует в клуб{ "ах" if len(t["clubs"]) > 1 else "е"}</h2>{clubs}</div>'
            '<p class="profile-booking-note">Администратор подскажет свободное время и поможет записаться на тренировку.</p>'
            f'<a class="text-link profile-back" href="/trainers/">Вся команда {ARROW}</a></div></section>'
            '<section class="section trainer-about-section" aria-labelledby="trainer-about-title"><div class="container trainer-about-layout">'
            '<div><p class="eyebrow">ОПЫТ / ПОДХОД / ДОСТИЖЕНИЯ</p><span class="accent-line" aria-hidden="true"></span>'
            '<h2 id="trainer-about-title">О ТРЕНЕРЕ.</h2></div>'
            f'<div class="trainer-biography">{t["description_html"]}</div></div></section>{photos}'
            '<dialog class="trainer-photo-dialog" id="trainer-photo-dialog" aria-label="Фотографии тренера">'
            '<button type="button" class="dialog-close" data-close-trainer-photo aria-label="Закрыть фотографию">×</button>'
            f'<figure><img id="trainer-photo-full" alt="{e(t["name"])}"><figcaption id="trainer-photo-caption"></figcaption></figure>'
            '<div class="trainer-photo-controls"><button type="button" data-trainer-photo-prev aria-label="Предыдущее фото">←</button>'
            '<span id="trainer-photo-count" aria-live="polite"></span><button type="button" data-trainer-photo-next aria-label="Следующее фото">→</button></div></dialog>')


directory_path = SITE / 'trainers/index.html'
directory = directory_path.read_text()
save(directory_path, replace_section(directory, r'class="section team-page"', directory_section()))

for cid in CLUBS:
    path = SITE / f'clubs/{cid}/index.html'
    text = path.read_text()
    if 'id="trainers"' in text:
        text = replace_section(text, r'id="trainers"', club_section(cid))
    else:
        target = '<section class="section gallery-section">'
        assert text.count(target) == 1
        text = text.replace(target, club_section(cid) + target, 1)
    hero_end = text.index('</section>', text.index('<section class="club-hero'))
    hero = text[:hero_end]
    if 'class="text-link club-team-jump"' not in hero:
        anchor = f'<a class="text-link club-team-jump" href="#trainers">Тренеры клуба {ARROW}</a>'
        text = text[:hero_end].replace('</div></div><figure>', anchor + '</div></div><figure>', 1) + text[hero_end:]
    save(path, text)

home_path = SITE / 'index.html'
home = home_path.read_text()
section = re.search(r'<section\b[^>]*id="team"[\s\S]*?</section>', home).group(0)
def update_home_card(match):
    tid = re.search(r'href="/trainers/([^/]+)/"', match.group(0)).group(1)
    return card(TRAINERS[tid])
section = re.sub(r'<a class="trainer-card"[^>]*>[\s\S]*?</a>', update_home_card, section)
save(home_path, replace_section(home, r'id="team"', section))

for tid, t in TRAINERS.items():
    path = SITE / f'trainers/{tid}/index.html'
    text = path.read_text()
    # Keep the current membership block; its offers are scoped to this trainer
    # by refresh-memberships.py after the current club assignments are written.
    remainder = re.search(r'<main id="main">[\s\S]*?(<section\b[^>]*\bid="cards"[^>]*>[\s\S]*?)</main>', text).group(1)
    text = re.sub(r'(<main id="main">)[\s\S]*?(</main>)', lambda m: m.group(1) + profile(t) + remainder + m.group(2), text, count=1)
    save(path, text)

CONTENT['trainers'] = [{k: t[k] for k in ['id', 'name', 'speciality', 'image', 'clubs', 'bio', 'source']} for t in TRAINERS.values()]
for c in CONTENT['clubs']:
    c['trainers'] = next(s['trainers'] for s in DATA['club_sources'] if s['id'] == c['id'])
CONTENT_PATH.write_text(prefix + json.dumps(CONTENT, ensure_ascii=False) + ';\n')
# Content is also used by shared club / membership controls. Refresh its URL on
# every page so a cached older JS object cannot restore an obsolete trainer list.
version = hashlib.sha256(CONTENT_PATH.read_bytes()).hexdigest()[:12]
for path in SITE.rglob('*.html'):
    text = path.read_text()
    text = re.sub(r'src="/assets/content\.js(?:\?[^" ]*)?"', f'src="/assets/content.js?v={version}"', text)
    path.write_text(text)
runpy.run_path(str(ROOT / '.github/scripts/refresh-memberships.py'), run_name='__main__')
print('Rendered', len(TRAINERS), 'complete trainer profiles and', len(CLUBS), 'club rosters.')
