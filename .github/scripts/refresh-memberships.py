#!/usr/bin/env python3
"""Render membership offers according to each page's club context.

The full shared catalog supplies the unchanged prices, options and card markup.
Trainer contexts come from their current assignments, including owner overrides.
"""
from pathlib import Path
from html import escape
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'new-site'
RULES = json.loads((SITE / 'data/membership-rules.json').read_text())
TRAINERS = json.loads((SITE / 'data/trainers.json').read_text())['trainers']
CONTENT_PATH = SITE / 'assets/content.js'
PREFIX = 'window.LS_DATA = '
CONTENT = json.loads(CONTENT_PATH.read_text().removeprefix(PREFIX).strip().removesuffix(';'))
CLUBS = {c['id']: c for c in CONTENT['clubs']}
SECTION = r'<section\b[^>]*\bid="cards"[^>]*>[\s\S]*?</section>'
CATALOG = re.search(SECTION, (SITE / 'cards/index.html').read_text()).group(0)
END = '</div></section>'
detail_start = CATALOG.index('<div class="price-detail">')
assert CATALOG.endswith(END)
CATALOG_DETAILS = CATALOG[detail_start:-len(END)]
CATALOG = CATALOG[:detail_start] + END
assert len(re.findall(r'<article\b[^>]*class="membership (?:graphite|green)"', CATALOG)) == 2
assert set(RULES['cards']['graphite']['club_ids']) == set(CLUBS)
assert RULES['cards']['green']['club_ids'] == ['kuibysheva']


def sub_once(pattern, replacement, text):
    result, count = re.subn(pattern, lambda _: replacement, text, count=1)
    if count != 1:
        raise ValueError('Expected one match: ' + pattern)
    return result


def render_section(club_ids, full=False):
    assert club_ids and set(club_ids) <= set(CLUBS)
    available = [key for key, rule in RULES['cards'].items() if set(club_ids) & set(rule['club_ids'])]
    assert available in [['graphite'], ['graphite', 'green']]
    single = available == ['graphite']
    text = CATALOG
    if single:
        text = sub_once(r'<article class="membership green"[^>]*>[\s\S]*?</article>', '', text)
    cls = 'section cards-section' + (' cards-section-single' if single else '')
    text = sub_once(r'<section\b[^>]*>', f'<section class="{cls}" id="cards" data-card-clubs="{" ".join(club_ids)}">', text)
    text = sub_once(r'class="memberships(?: memberships-single)?"', 'class="memberships' + (' memberships-single' if single else '') + '"', text)
    if single:
        names = ' и '.join(CLUBS[c]['street'] for c in club_ids)
        intro = ('В клубе' if len(club_ids) == 1 else 'В клубах') + ' на ' + names + ' действует Графитовая карта. Выберите время и срок посещения.'
        note = 'Графитовая карта действует во всех клубах сети, включая ' + names + '.'
    elif club_ids == ['kuibysheva']:
        intro = 'На Куйбышева, 60 действуют обе карты: Графитовая и Зелёная. Выберите время и срок посещения.'
        note = 'Зелёная карта — только для Куйбышева, 60. Графитовая также подходит для всех остальных клубов сети.'
    else:
        intro = 'Графитовая карта — для всех клубов сети. Зелёная — только для Куйбышева, 60. Выберите время и срок посещения.'
        note = 'Графитовая карта действует во всех клубах сети. Зелёная карта действует только на Куйбышева, 60.'
    text = sub_once(r'<p class="section-intro">[\s\S]*?</p>', '<p class="section-intro">' + escape(intro) + '</p>', text)
    text = sub_once(r'<div class="card-notes"><p>[\s\S]*?</p>', '<div class="card-notes"><p>' + escape(note) + '</p>', text)
    if full:
        text = text[:-len(END)] + CATALOG_DETAILS + END
    else:
        assert '<h1 class="page-heading">' in text
        text = text.replace('<h1 class="page-heading">', '<h2>', 1).replace('</h1>', '</h2>', 1)
        arrow = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'
        footer = '<div class="card-notes"><p>' + escape(note) + '</p><a class="text-link" href="/cards/">Все тарифы и условия ' + arrow + '</a></div>'
        text = sub_once(r'<div class="card-notes">[\s\S]*?</div>', footer, text)
    return text, available


scope_css_version = hashlib.sha256((SITE / 'assets/membership-scope.css').read_bytes()).hexdigest()[:12]
scope_link = f'<link rel="stylesheet" href="/assets/membership-scope.css?v={scope_css_version}">'
contexts = {'index.html': list(CLUBS), 'cards/index.html': list(CLUBS)}
contexts.update({f'clubs/{cid}/index.html': [cid] for cid in CLUBS})
contexts.update({f'directions/{did}/index.html': ids for did, ids in RULES['direction_clubs'].items()})
contexts.update({f'trainers/{t["id"]}/index.html': t['clubs'] for t in TRAINERS})
counts = {'graphite_only': 0, 'both': 0}
for rel, club_ids in contexts.items():
    path = SITE / rel
    text = path.read_text()
    section, cards = render_section(club_ids, full=rel == 'cards/index.html')
    if re.search(SECTION, text):
        text = sub_once(SECTION, section, text)
    elif rel.startswith('clubs/'):
        target = '<section class="section contacts-section"'
        assert text.count(target) == 1, rel
        text = text.replace(target, section + target, 1)
    else:
        raise ValueError('Missing membership section: ' + rel)
    text = re.sub(r'<link\b[^>]*href="/assets/membership-scope\.css(?:\?[^" ]*)?"[^>]*>', '', text)
    text = text.replace('</head>', scope_link + '</head>', 1)
    if rel.startswith('clubs/'):
        cid = rel.split('/')[1]
        if cid == 'heroes':
            note = 'В клубе на Героев Сталинграда, 6Д действует Графитовая карта. Она также подходит для остальных клубов сети.'
            CONTENT['clubs'][list(CLUBS).index(cid)]['note'] = note
            text = sub_once(r'<p class="club-notice">[\s\S]*?</p>', '<p class="club-notice">' + note + '</p>', text)
        hero = re.search(r'<section class="club-hero[\s\S]*?</section>', text).group(0)
        updated_hero = hero.replace('href="/cards/"', 'href="#cards"', 1)
        text = text.replace(hero, updated_hero, 1)
    path.write_text(text)
    counts['graphite_only' if len(cards) == 1 else 'both'] += 1

# The shared FAQ must express the same current rule as the contextual offers.
home_path = SITE / 'index.html'
home = home_path.read_text()
old_faq = 'Графитовая карта даёт доступ во все действующие клубы сети. Зелёная — локальный формат. В клубе на Героев Сталинграда, 6Д принимают Графитовые карты, а также действующие Зелёные карты, ранее приобретённые на Героев Сталинграда, 10, до окончания их срока.'
home = home.replace(old_faq, 'Графитовая карта даёт доступ во все клубы сети. Зелёная карта действует только в клубе на Куйбышева, 60. В этом клубе можно заниматься по любой из двух карт.')
home_path.write_text(home)
CONTENT['pricing_rules']['card_access'] = {key: rule['club_ids'] for key, rule in RULES['cards'].items()}
CONTENT_PATH.write_text(PREFIX + json.dumps(CONTENT, ensure_ascii=False) + ';\n')
content_version = hashlib.sha256(CONTENT_PATH.read_bytes()).hexdigest()[:12]
for path in SITE.rglob('*.html'):
    text = path.read_text()
    text = re.sub(r'src="/assets/content\.js(?:\?[^" ]*)?"', f'src="/assets/content.js?v={content_version}"', text)
    path.write_text(text)
print('Rendered membership contexts:', counts)
