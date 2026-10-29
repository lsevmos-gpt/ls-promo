#!/usr/bin/env python3
"""Prepare and verify a bounded update to existing public text files only."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha1, sha256
from pathlib import Path
import json
import os
import re
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / '_new_site_text_patch.json'
BACKUP = ROOT / '_new_site_remote_backup'
ORIGIN = 'https://new.liniyasporta.ru'
ALLOWED = re.compile(r'new-site/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:html|css|js|json)')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def prepare():
    base, commit = os.environ['PATCH_BASE_SHA'], os.environ['GITHUB_SHA']
    if not all(re.fullmatch('[a-f0-9]{40}', value) for value in [base, commit]):
        raise SystemExit('Invalid patch commit identifiers.')
    rows = git('diff', '--name-status', '--no-renames', base, commit, '--', 'new-site/').splitlines()
    if not 1 <= len(rows) <= 50:
        raise SystemExit('Text update must contain 1–50 existing public files.')
    files, size = [], 0
    for row in rows:
        status, path = row.split('\t', 1)
        source = ROOT / path
        if (status != 'M' or not ALLOWED.fullmatch(path) or '..' in Path(path).parts
                or not source.is_file() or source.is_symlink()
                or not source.resolve().is_relative_to(ROOT)):
            raise SystemExit('Unsupported text update path or change: ' + row)
        body = source.read_bytes()
        size += len(body)
        if len(body) > 512 * 1024 or size > 2 * 1024 * 1024:
            raise SystemExit('Text update exceeds the size limit; use a full deployment.')
        files.append({'path': path, 'remote': path.removeprefix('new-site/'),
                      'before_blob': git('rev-parse', base + ':' + path),
                      'sha256': sha256(body).hexdigest()})
    PLAN.write_text(json.dumps({'base': base, 'commit': commit, 'files': files}, indent=2))
    backup_commands, upload_commands = [], []
    for item in files:
        relative = item['remote']
        destination = BACKUP / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        backup_commands.append(f'get "{relative}" -o "_new_site_remote_backup/{relative}";')
        upload_commands.append(f'put "{item["path"]}" -o "{relative}";')
    (ROOT / '_new_site_patch_backup.lftp').write_text('\n'.join(backup_commands) + '\n')
    (ROOT / '_new_site_patch_upload.lftp').write_text('\n'.join(upload_commands) + '\n')
    print(f'Prepared {len(files)} existing text files, {size} bytes. Other hosting files are outside this update.')

def verify_backup():
    plan = json.loads(PLAN.read_text())
    for item in plan['files']:
        body = (BACKUP / item['remote']).read_bytes()
        blob = sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
        if blob != item['before_blob']:
            raise SystemExit('Hosting differs from the expected version; no upload authorized: ' + item['remote'])
    print('All downloaded backup files match the expected previous commit. Upload may proceed.')

def verify_live():
    plan = json.loads(PLAN.read_text())
    def check(item):
        request = Request(ORIGIN + '/' + item['remote'] + '?patch=' + plan['commit'],
                          headers={'Cache-Control': 'no-cache'})
        with urlopen(request, timeout=35) as response:
            body = response.read()
        if sha256(body).hexdigest() != item['sha256']:
            raise SystemExit('Published file does not match: ' + item['remote'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(check, plan['files']))
    print(f'All {len(plan["files"])} updated public files match over HTTPS.')

if __name__ == '__main__':
    actions = {'prepare': prepare, 'verify-backup': verify_backup, 'verify-live': verify_live}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('Choose prepare, verify-backup, or verify-live.')
    actions[sys.argv[1]]()
