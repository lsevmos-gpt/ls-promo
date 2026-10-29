#!/usr/bin/env python3
"""Render confirmed club addresses and hours in all current contact details."""
from pathlib import Path
from html import escape
import hashlib
import json
import re
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'new-site'
CONTENT = SITE / 'assets/content.js'
PREFIX = 'window.LS_DATA = '
data = json.loads(CONTENT.read_text().removeprefix(PREFIX).strip().removesuffix(';'))
clubs = {club['id']: club for club in data['clubs']}
phones = {club['tel']: club for club in data['clubs']}

def canonical_address(text):
    # Current club labels follow the owner's latest address. Original biographies
    # retain their sourced wording and are not used as current contact labels.
    biographies = []
    def protect(match):
        biographies.append(match.group())
        return f'__CLUB_HOURS_BIO_{len(biographies) - 1}__'
    text = re.sub(r'<div class="trainer-biography">[\s\S]*?</div></div></section>', protect, text)
    text = re.sub(r'1-й Конной Армии, 25(?![АAаa0-9])', '1-й Конной Армии, 25А', text)
    text = re.sub(r'(%D0%9A%D0%BE%D0%BD%D0%BD%D0%BE%D0%B9%20%D0%90%D1%80%D0%BC%D0%B8%D0%B8%2C%2025)(?!%D0%90|A|[0-9])', r'\1%D0%90', text, flags=re.I)
    for i, biography in enumerate(biographies):
        text = text.replace(f'__CLUB_HOURS_BIO_{i}__', biography)
    return text

contact_count = explorer_count = club_page_count = 0
for path in SITE.rglob('*.html'):
    text = canonical_address(path.read_text())
    def contact(match):
        global contact_count
        row = match.group()
        phone = re.search(r'class="contact-phone" href="tel:([^"]+)"', row)
        assert phone and phone[1] in phones, path
        club = phones[phone[1]]
        row = re.sub(r'<p(?: class="contact-(?:address|hours)")?>[\s\S]*?</p>', '', row)
        details = ('<p class="contact-address">' + escape(club['address']) + '</p>'
                   '<p class="contact-hours">' + escape(club['hours']) + '</p>')
        row, count = re.subn(r'</h3>', '</h3>' + details, row, count=1)
        assert count == 1, path
        contact_count += 1
        return row
    text = re.sub(r'<article class="contact-row">[\s\S]*?</article>', contact, text)
    if 'id="club-panel"' in text:
        initial_name = re.search(r'<h3 id="club-title">([^<]+)</h3>', text)[1]
        club = next(c for c in clubs.values() if c['street'] == initial_name)
        address = '<p class="club-postal-address" id="club-address">' + escape(club['address']) + '</p>'
        text = re.sub(r'<p class="club-postal-address" id="club-address">[\s\S]*?</p>', '', text)
        text, count = re.subn(r'<p id="club-lead">', lambda m: address + m.group(), text, count=1)
        assert count == 1, path
        def club_tab(match):
            tab = match.group()
            cid = re.search(r'data-club="([^"]+)"', tab)[1]
            tab, count = re.subn(r'<small>[\s\S]*?</small>', '<small>' + escape(clubs[cid]['address']) + '</small>', tab, count=1)
            assert count == 1, path
            return tab
        text = re.sub(r'<button\b[^>]*data-club="[^"]+"[^>]*>[\s\S]*?</button>', club_tab, text)
        hours = '<p class="club-hours" id="club-hours">Режим работы: ' + escape(club['hours']) + '</p>'
        if 'id="club-hours"' in text:
            text, count = re.subn(r'<p class="club-hours" id="club-hours">[\s\S]*?</p>', lambda _: hours, text, count=1)
        else:
            text, count = re.subn(r'<p id="club-lead">[\s\S]*?</p>', lambda m: m.group() + hours, text, count=1)
        assert count == 1, path
        explorer_count += 1
    if path.parent.parent == SITE / 'clubs':
        club = clubs[path.parent.name]
        text, count = re.subn(r'<p class="club-address">[\s\S]*?</p>', '<p class="club-address">' + escape(club['address']) + '</p>', text, count=1)
        assert count == 1, path
        note = '<p class="club-notice">' + escape(club['note']) + '</p>'
        text, count = re.subn(r'<p class="club-notice">[\s\S]*?</p>', lambda _: note, text, count=1)
        assert count == 1, path
        text = re.sub(r'<p class="hours">[\s\S]*?</p>', '', text)
        hours = '<p class="hours"><strong>Режим работы</strong><br>' + escape(club['hours']) + '</p>'
        text = text.replace(note, note + hours, 1)
        club_page_count += 1
    def map_link(match):
        query = unquote(match[1])
        club = next((c for c in clubs.values() if c['street'] in query or c['street_address'] in query), None)
        return 'href="https://yandex.ru/maps/?text=' + quote(club['address'] if club else query, safe='') + '"'
    text = re.sub(r'href="https://yandex.ru/maps/\?text=([^"]+)"', map_link, text)
    def structured_data(match):
        schema = json.loads(match[1])
        for location in schema.get('subOrganization', []):
            cid = location.get('url', '').rstrip('/').split('/')[-1]
            if cid not in clubs:
                continue
            club = clubs[cid]
            location['address'].update(addressRegion='Республика Крым', addressLocality='Симферополь', streetAddress=club['street_address'])
            location['openingHours'] = ['Mo-Sa 07:00-23:00', 'Su 09:00-' + ('17:00' if cid == 'kuibysheva' else '19:00')]
        return '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False) + '</script>'
    text = re.sub(r'<script type="application/ld\+json">([\s\S]*?)</script>', structured_data, text)
    # Cache fingerprints also cover pages that only use the shared JS data.
    for asset, attr, required in [('assets/content.js', 'src', True), ('app.js', 'src', True),
                                  ('assets/trainers.css', 'href', False), ('assets/trainer-passes.css', 'href', False)]:
        filename = SITE / asset
        digest = hashlib.sha256(filename.read_bytes()).hexdigest()[:12]
        text, count = re.subn(attr + r'="/' + re.escape(asset) + r'(?:\?[^" ]*)?"', attr + '="/' + asset + '?v=' + digest + '"', text)
        assert count == 1 if required else count <= 1, (path, asset)
    path.write_text(text)

print(f'Rendered addresses and hours in {contact_count} contact rows, {explorer_count} club explorers and {club_page_count} club pages; refreshed all page fingerprints.')
