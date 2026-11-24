#!/usr/bin/env python3
"""Safely patch ONLY the live BF banner into the existing REG.RU homepage.

Never replace the remote page with stale source files. Abort on changed anchors.
"""
from pathlib import Path
from hashlib import sha256
import re

P = Path('_bf_live_patch')
original = (P/'remote-index.html').read_bytes()
stylesheet = (P/'remote-promotions.css').read_bytes()
actual_page = (P/'public-index.html').read_bytes()
if original != actual_page:
    raise SystemExit('STOP: Public main domain does not match REG.RU remote index; do not overwrite')
try:
    html=original.decode('utf-8')
    css=stylesheet.decode('utf-8')
except UnicodeDecodeError:
    raise SystemExit('STOP: Remote files are not UTF-8')
anchor='<div class="hp3-grid">'
if html.count(anchor)!=1 or 'id="promotions"' not in html or 'hp3-discount' not in html or 'hp3-friend' not in html:
    raise SystemExit('STOP: Promotions section changed; banner cannot be inserted safely')
if '<!-- BLACK FRIDAY 2026 BEGIN' in html or '.bf26-home-feature' in css:
    raise SystemExit('STOP: Another Black Friday banner already installed; do not duplicate')
html_snippet=Path('.github/black-friday-2026/home-banner.html').read_text(encoding='utf-8').strip()
css_snippet=Path('.github/black-friday-2026/home-banner.css').read_text(encoding='utf-8').strip()
if '<!-- BLACK FRIDAY 2026 BEGIN' not in html_snippet or 'bf26-home-feature' not in css_snippet:
    raise SystemExit('STOP: Invalid banner snippet')
result=html.replace(anchor,html_snippet+'\n'+anchor,1)
result_css=css.rstrip()+'\n\n'+css_snippet+'\n'
if any(result.count(w)<1 for w in ['hp3-discount','hp3-friend','black-friday-2026-hero.webp']):
    raise SystemExit('STOP: Promotions lost unexpectedly')
if len(result)>1000000 or len(result_css)>500000:
    raise SystemExit('STOP: Oversized patched files')
(P/'patched-index.html').write_bytes(result.encode('utf-8'))
(P/'patched-promotions.css').write_bytes(result_css.encode('utf-8'))
for p in ['new-site/assets/campaigns/black-friday-2026-hero.webp','new-site/assets/campaigns/black-friday-2026-card.webp','new-site/assets/campaigns/black-friday-2026-mobile.webp']:
    b=Path(p).read_bytes()
    if not(b.startswith(b'RIFF') and b[8:12]==b'WEBP'):
        raise SystemExit('Invalid WebP '+p)
print('READY_FOR_BOUNDED_UPDATE remote_html_original_sha256='+sha256(original).hexdigest())
print('READY_FOR_BOUNDED_UPDATE new_html_sha256='+sha256((P/'patched-index.html').read_bytes()).hexdigest())
