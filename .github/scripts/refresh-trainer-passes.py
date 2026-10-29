#!/usr/bin/env python3
"""Render owner-supplied trainer tariffs without changing club cards or bios."""
from pathlib import Path
from html import escape
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'new-site'
DATA = json.loads((SITE / 'data/trainer-passes.json').read_text())
TRAINERS = json.loads((SITE / 'data/trainers.json').read_text())['trainers']
CONTENT = json.loads((SITE / 'assets/content.js').read_text().removeprefix('window.LS_DATA = ').strip().removesuffix(';'))
CLUBS = {c['id']: c for c in CONTENT['clubs']}
START = '<!-- TRAINER_PASSES_START -->'
END = '<!-- TRAINER_PASSES_END -->'
UP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5M5 5h14v14"/></svg>'
DOWN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v16M5 13l7 7 7-7"/></svg>'
SYMBOLS = {
    'mini': '<svg class="trainer-pass-symbol" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="12" r="4"/><circle cx="8" cy="16" r="3"/><circle cx="32" cy="16" r="3"/><path d="M12 33v-5a8 8 0 0 1 16 0v5M3 33v-5a5 5 0 0 1 6-5M37 33v-5a5 5 0 0 0-6-5"/></svg>',
    'individual': '<svg class="trainer-pass-symbol" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="12" r="5"/><path d="M10 33v-4a10 10 0 0 1 20 0v4"/></svg>',
}
assert DATA['sessions'] == [8, 12]
assert DATA['default_sessions'] == 8
assert [(f['id'], f['prices']) for f in DATA['formats']] == [
    ('mini', {'8': 6000, '12': 7000}), ('individual', {'8': 11000, '12': 13000})]

def amount(value):
    return f'{value:,}'.replace(',', '\u00a0')

def block(*, embedded, heading, href, cta):
    cards = ''
    for f in DATA['formats']:
        name_heading = heading + 1
        cards += (f'<article class="membership trainer-pass" data-trainer-pass="{f["id"]}" data-price8="{f["prices"]["8"]}" data-price12="{f["prices"]["12"]}">'
                  '<div class="membership-heading"><span class="membership-label">ТРЕНЕРСКИЙ АБОНЕМЕНТ</span>' + SYMBOLS[f['id']] + '</div>'
                  f'<h{name_heading} class="trainer-pass-name">{f["title"]}</h{name_heading}>'
                  f'<p class="trainer-pass-description">{f["description"]}</p>'
                  f'<p class="trainer-pass-price"><strong data-trainer-price>{amount(f["prices"]["8"])}</strong><span>₽</span></p>'
                  '<p class="trainer-pass-quantity" data-trainer-quantity>За 8 тренировок с тренером</p>'
                  f'<div class="trainer-pass-footer"><a class="button button-primary" href="{escape(href)}">{escape(cta)} {UP}</a></div></article>')
    inner = ('<div class="trainer-passes-head"><div><p class="eyebrow">СТОИМОСТЬ УСЛУГ ТРЕНЕРА</p>'
             f'<h{heading} class="trainer-passes-title" id="trainer-passes-title">АБОНЕМЕНТЫ<br>С ТРЕНЕРОМ.</h{heading}></div>'
             '<p class="trainer-passes-intro">Выберите количество тренировок и удобный формат занятий с тренером.</p></div>'
             '<div class="trainer-passes-controls"><div class="segment" role="group" aria-label="Количество тренировок с тренером">'
             '<button type="button" class="active" data-trainer-sessions="8" aria-pressed="true" disabled>8 тренировок</button>'
             '<button type="button" data-trainer-sessions="12" aria-pressed="false" disabled>12 тренировок</button></div>'
             '<p>Стоимость указана за весь абонемент.</p></div>'
             f'<div class="trainer-pass-grid" aria-live="polite" aria-atomic="true">{cards}</div>'
             '<p class="trainer-passes-note">В мини-группе тренер занимается с несколькими клиентами одновременно — до трёх человек. '
             'Индивидуальная тренировка проходит один на один. Время занятий согласуйте с тренером или администратором клуба.</p>'
             '<noscript><p class="trainer-passes-noscript">12 тренировок: мини-группа — 7 000 ₽, индивидуально — 13 000 ₽.</p></noscript>')
    if embedded:
        markup = ('<div class="trainer-passes trainer-passes--embedded" id="trainer-passes" data-trainer-passes '
                  f'role="region" aria-labelledby="trainer-passes-title">{inner}</div>')
    else:
        markup = ('<section class="section trainer-passes trainer-passes--section" data-trainer-passes '
                  f'aria-labelledby="trainer-passes-title"><div class="container" id="trainer-passes">{inner}</div></section>')
    return START + markup + END

JUMP = '<a class="trainer-pass-jump" href="#trainer-passes">Абонементы и стоимость ' + DOWN + '</a>'

def clean(text):
    text = re.sub(re.escape(START) + r'[\s\S]*?' + re.escape(END), '', text)
    return re.sub(r'<a class="trainer-pass-jump"[^>]*>[\s\S]*?</a>', '', text)

def assets(text):
    for filename in ['trainer-passes.css', 'trainer-passes.js']:
        text = re.sub(rf'<(?:link|script)\b[^>]*(?:href|src)="/assets/{re.escape(filename)}(?:\?[^" ]*)?"[^>]*>(?:</script>)?', '', text)
        version = hashlib.sha256((SITE / 'assets' / filename).read_bytes()).hexdigest()[:12]
        tag = (f'<link rel="stylesheet" href="/assets/{filename}?v={version}">' if filename.endswith('.css')
               else f'<script src="/assets/{filename}?v={version}" defer></script>')
        text = text.replace('</head>', tag + '</head>', 1)
    return text

def add_to_roster(path, marker, *, href, cta, heading):
    text = clean(path.read_text())
    pattern = rf'<section\b[^>]*{marker}[^>]*>[\s\S]*?</section>'
    match = re.search(pattern, text)
    assert match, path
    section = match.group()
    head_end = section.index('</p></div>', section.index('class="section-head"')) + len('</p></div>')
    # Put the shortcut directly after the roster introduction, ahead of the list.
    section = section[:head_end] + JUMP + section[head_end:]
    # No nested sections: the existing trainer renderer relies on this boundary.
    closing = '</div></section>'
    assert section.endswith(closing), path
    section = section[:-len(closing)] + block(embedded=True, heading=heading, href=href, cta=cta) + closing
    text = text[:match.start()] + section + text[match.end():]
    path.write_text(assets(text))

add_to_roster(SITE / 'index.html', 'id="team"', href='/trainers/', cta='Выбрать тренера', heading=3)
add_to_roster(SITE / 'trainers/index.html', 'class="section team-page"', href='#team-results', cta='Выбрать тренера', heading=2)
for cid, club in CLUBS.items():
    add_to_roster(SITE / f'clubs/{cid}/index.html', 'id="trainers"', href='tel:' + club['tel'], cta='Записаться в клубе', heading=3)

for trainer in TRAINERS:
    path = SITE / f'trainers/{trainer["id"]}/index.html'
    text = clean(path.read_text())
    if len(trainer['clubs']) == 1:
        href, cta = 'tel:' + CLUBS[trainer['clubs'][0]]['tel'], 'Записаться к тренеру'
    else:
        href, cta = '#trainer-clubs', 'Выбрать клуб для записи'
        text = text.replace('<div class="profile-availability">', '<div class="profile-availability" id="trainer-clubs">', 1)
    hero = re.search(r'<section\b[^>]*class="section trainer-profile[^>]*>[\s\S]*?</section>', text)
    assert hero, path
    section = hero.group()
    marker = '<a class="text-link profile-back"'
    assert marker in section
    section = section.replace(marker, JUMP + marker, 1)
    text = text[:hero.start()] + section + block(embedded=False, heading=2, href=href, cta=cta) + text[hero.end():]
    path.write_text(assets(text))

path = SITE / 'directions/personal/index.html'
text = clean(path.read_text())
hero = re.search(r'<section\b[^>]*class="section direction-page[^>]*>[\s\S]*?</section>', text)
assert hero
text = text[:hero.end()] + block(embedded=False, heading=2, href='/trainers/', cta='Выбрать тренера') + text[hero.end():]
path.write_text(assets(text))
print('Rendered trainer packages on 25 pages: home, directory, 3 clubs, 19 profiles and personal training.')
