"""Keep the main website stylesheet URL aligned with the exact CSS bytes."""
from pathlib import Path
from hashlib import sha256
import re
import sys

site = Path(__file__).resolve().parents[2] / 'new-site'
version = sha256((site / 'styles.css').read_bytes()).hexdigest()[:12]
check_only = '--check' in sys.argv[1:]
stale = []
pages = sorted(site.rglob('*.html'))
for page in pages:
    original = page.read_text()
    updated, count = re.subn(
        r'href=([\"\x27])/styles\.css(?:\?[^\"\x27]*)?\1',
        lambda match: 'href=' + match[1] + '/styles.css?v=' + version + match[1],
        original,
    )
    if count != 1:
        raise SystemExit('Expected one main stylesheet: ' + str(page.relative_to(site)))
    if updated != original:
        stale.append(page.relative_to(site).as_posix())
        if not check_only:
            page.write_text(updated)
if check_only and stale:
    raise SystemExit('Outdated CSS version in: ' + ', '.join(stale))
print(f'Main CSS version {version}; checked {len(pages)} HTML pages.')
