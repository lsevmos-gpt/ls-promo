"""Publish the approved single-file app landing page to its dedicated FTP root."""
from pathlib import Path
from hashlib import sha256
from urllib.request import Request, urlopen
import ftplib
import io
import json
import os
import ssl
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'app-site'
BACKUP = ROOT / '_app_site_backup'

def digest(data):
    return sha256(data).hexdigest()

def settings():
    config = json.loads((SITE / 'deployment.json').read_text())
    if config['origin'] != 'https://app.liniyasporta.ru' or config['ftp_host'] != 'server169.hosting.reg.ru':
        raise SystemExit('Unexpected deployment destination.')
    approved = (SITE / 'index.html').read_bytes()
    if digest(approved) != config['approved_sha256']:
        raise SystemExit('Approved source checksum mismatch.')
    if b'https://app.liniyasporta.ru/' not in approved:
        raise SystemExit('App domain missing from approved source.')
    return config, approved

def fetch_current(config, suffix):
    request = Request(config['origin'] + '/?' + suffix, headers={'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=35) as response:
        return response.read(2_000_001)

def connect(config):
    username = os.environ.get('APP_REG_USER', '').strip()
    password = os.environ.get('APP_REG_PASSWORD', '')
    if not username:
        raise SystemExit('Missing repository variable APP_REG_USER: dedicated FTP account for app.liniyasporta.ru.')
    if not password:
        raise SystemExit('Missing repository secret APP_REG_PASSWORD: password of the app domain FTP account.')
    ftp = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=35)
    ftp.connect(config['ftp_host'], 21)
    ftp.login(username, password)
    ftp.prot_p()
    ftp.set_pasv(True)
    ftp.cwd('/')
    return ftp

def read_index(ftp):
    output = io.BytesIO()
    def append(chunk):
        output.write(chunk)
        if output.tell() > 2_000_000:
            raise ValueError('Unexpected destination index size.')
    ftp.retrbinary('RETR index.html', append)
    return output.getvalue()

def backup(config):
    with connect(config) as ftp:
        existing = read_index(ftp)
    public = fetch_current(config, 'app-preflight=' + os.environ.get('GITHUB_RUN_ID', 'manual'))
    if digest(existing) != config['previous_sha256'] or public != existing:
        raise SystemExit('FTP index must match the expected app homepage over HTTPS. No writes performed.')
    BACKUP.mkdir(exist_ok=True)
    (BACKUP / 'index.html').write_bytes(existing)
    print('Dedicated app FTP root verified against HTTPS; original public homepage backed up.')

def deploy(config, approved):
    saved = (BACKUP / 'index.html').read_bytes()
    if digest(saved) != config['previous_sha256']:
        raise SystemExit('Verified backup missing or changed.')
    run_id = os.environ.get('GITHUB_RUN_ID', 'manual')
    if not run_id.isdigit() and run_id != 'manual':
        raise SystemExit('Unexpected run identifier.')
    temporary = '.app-index-upload-' + run_id + '.html'
    with connect(config) as ftp:
        if read_index(ftp) != saved:
            raise SystemExit('Destination changed after backup; publishing stopped before writing.')
        ftp.storbinary('STOR ' + temporary, io.BytesIO(approved), blocksize=131072)
        ftp.rename(temporary, 'index.html')
    print('Approved app homepage published; other remote files untouched.')

def verify(config, approved):
    last = None
    for attempt in range(6):
        try:
            public = fetch_current(config, 'app-deploy=' + os.environ.get('GITHUB_SHA', 'manual'))
            if public != approved:
                raise ValueError('Live homepage bytes differ from approved source.')
            print('HTTPS_VERIFIED https://app.liniyasporta.ru/ SHA256=' + digest(public))
            return
        except Exception as exc:
            last = exc
            if attempt < 5:
                time.sleep(4)
    raise SystemExit('Publication verification failed: ' + str(last))

if __name__ == '__main__':
    config, approved = settings()
    phase = sys.argv[1] if len(sys.argv) == 2 else ''
    if phase == 'backup':
        backup(config)
    elif phase == 'deploy':
        deploy(config, approved)
    elif phase == 'verify':
        verify(config, approved)
    else:
        raise SystemExit('Expected backup, deploy or verify phase.')
