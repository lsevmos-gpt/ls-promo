#!/usr/bin/env python3
"""Prepare and verify a bounded update to text files and new trainer images."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha1, sha256
from pathlib import Path
import json
import os
import re
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / '_new_site_text_patch.json'
BACKUP = ROOT / '_new_site_remote_backup'
ORIGIN = 'https://new.liniyasporta.ru'
ALLOWED = re.compile(r'new-site/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:html|css|js|json)')
NEW_TRAINER_IMAGE = re.compile(r'new-site/assets/trainers/[A-Za-z0-9_.-]+-([a-f0-9]{10})\.webp')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def prepare():
    base, commit = os.environ['PATCH_BASE_SHA'], os.environ['GITHUB_SHA']
    if not all(re.fullmatch('[a-f0-9]{40}', value) for value in [base, commit]):
        raise SystemExit('Invalid patch commit identifiers.')
    rows = git('diff', '--name-status', '--no-renames', base, commit, '--', 'new-site/').splitlines()
    if not 1 <= len(rows) <= 50:
        raise SystemExit('Bounded update must contain 1–50 public files.')
    files, size = [], 0
    for row in rows:
        status, path = row.split('\t', 1)
        source = ROOT / path
        new_image = status == 'A' and NEW_TRAINER_IMAGE.fullmatch(path)
        existing_text = status == 'M' and ALLOWED.fullmatch(path)
        if (not (existing_text or new_image) or '..' in Path(path).parts
                or not source.is_file() or source.is_symlink()
                or not source.resolve().is_relative_to(ROOT)):
            raise SystemExit('Unsupported text update path or change: ' + row)
        body = source.read_bytes()
        if new_image:
            if (not body.startswith(b'RIFF') or body[8:12] != b'WEBP'
                    or new_image.group(1) != sha256(body).hexdigest()[:10]):
                raise SystemExit('Invalid or incorrectly fingerprinted trainer image: ' + path)
            try:
                request = Request(ORIGIN + '/' + path.removeprefix('new-site/') + '?before=' + commit,
                                  headers={'Cache-Control': 'no-cache'})
                with urlopen(request, timeout=35) as response:
                    if sha256(response.read()).hexdigest() != sha256(body).hexdigest():
                        raise SystemExit('New image URL already contains different content: ' + path)
            except HTTPError as error:
                if error.code != 404:
                    raise
        size += len(body)
        if len(body) > 512 * 1024 or size > 2 * 1024 * 1024:
            raise SystemExit('Text update exceeds the size limit; use a full deployment.')
        files.append({'path': path, 'remote': path.removeprefix('new-site/'),
                      'before_blob': None if new_image else git('rev-parse', base + ':' + path),
                      'sha256': sha256(body).hexdigest()})
    PLAN.write_text(json.dumps({'base': base, 'commit': commit, 'files': files}, indent=2))
    backup_commands, upload_commands = [], []
    # Publish images before any page can reference them.
    for item in sorted(files, key=lambda value: (value['before_blob'] is not None, value['remote'])):
        relative = item['remote']
        destination = BACKUP / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if item['before_blob'] is not None:
            backup_commands.append(f'get "{relative}" -o "_new_site_remote_backup/{relative}";')
        upload_commands.append(f'put "{item["path"]}" -o "{relative}";')
    (ROOT / '_new_site_patch_backup.lftp').write_text('\n'.join(backup_commands) + '\n')
    (ROOT / '_new_site_patch_upload.lftp').write_text('\n'.join(upload_commands) + '\n')
    print(f'Prepared {len(files)} public files, {size} bytes. New trainer images upload before text references.')

def verify_backup():
    plan = json.loads(PLAN.read_text())
    for item in plan['files']:
        if item['before_blob'] is None:
            continue
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
