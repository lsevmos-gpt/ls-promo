"""Reconstruct approved static export from the public club-site preview.

All non-WOFF2 source files are validated against an SHA-256 aggregate computed
from the owner-approved 2026-10-28 ZIP. No FTP actions occur in this script.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, quote
from urllib.request import Request, urlopen
import re
import time
import xml.etree.ElementTree as ET

SRC = "https://liniya-sporta-clubs.zippy-joy-1488.chatgpt.site"
DEST = "https://new.liniyasporta.ru"
ROOT = Path("new-site")
EXPECTED_HASH = "d831d22e4fc8956e2ba8d01fac0382eb2d75116435363b20236dec3d17b9801c"
GENERATED_FONTS = {f"assets/fonts/font-{n}.woff2" for n in range(5)}
GROUPS = {
    "brand": """fitness-burgundy.png fitness-dark.png fitness-white.png logo-dark.png logo-green.png logo-white.png""",
    "fitness": """aerostretching.webp fit-mix.webp functional.webp healthy-back.webp jumping-fitness.webp lady-dance.webp pilates.webp stretching.webp tabata.webp womens-health.webp yoga.webp""",
    "fonts": """font-0.woff2 font-1.woff2 font-2.ttf font-2.woff2 font-3.ttf font-3.woff2 font-4.ttf font-4.woff2 fonts.css inter-OFL.txt robotocondensed-OFL.txt""",
    "images": """app-original.png heroes6d-0-small.webp heroes6d-0.webp heroes6d-1-small.webp heroes6d-1.webp home-10-dsc07408_2x.webp home-11-dsc07882_2x.webp home-12-dsc07194_2x.webp home-13-dsc09428_2x.webp home-14-dsc07482_2x.webp home-15-dsc09607_2x.webp home-16-dsc06480_2x.webp home-17-dsc08464_2x.webp home-18-dsc07211_2x.webp home-19-dsc08521_2x.webp home-20-dsc09602_2x.webp home-21-dsc08481_2x.webp home-22-dsc07635_2x.webp home-23-dsc08929_2_2x.webp home-24-dsc09503_2_2x.webp home-25-dsc08959_2_2x.webp home-26-dsc08508_2x.webp home-27-1212_2x.webp home-5-ze4xk9gepvu_2x.webp home-6-dsc09996_2x.webp home-7-atm9rezvsi4_2x.webp home-8-dsc08251_2x.webp home-9-dsc07232_2x.webp konnoi-1-dsc09965_2x.webp konnoi-10-us6a5dglabw_2x.webp konnoi-11-zbnxk11u9ym_2x.webp konnoi-12-kjke1fyxlrm_2x.webp konnoi-13-dsc08771_hdr_2x.webp konnoi-14-dsc08251_2x.webp konnoi-15-dsc08521_2x.webp konnoi-16-dsc09602_2x.webp konnoi-17-dsc08481_2x.webp konnoi-18-dsc07635_2x.webp konnoi-19-dsc08929_2_2x.webp konnoi-2-dsc09996_2x.webp konnoi-20-dsc09503_2_2x.webp konnoi-21-dsc08959_2_2x.webp konnoi-22-dsc08503_2x.webp konnoi-3-dsc09980_2x.webp konnoi-4-dsc09988_2x.webp konnoi-5-dsc08718_hdr_2x.webp konnoi-6-dsc08736_hdr_2x.webp konnoi-7-dsc08814_hdr_2x.webp konnoi-8-dsc08747_hdr_2x.webp konnoi-9-dsc08709_hdr_2x.webp kuibysheva-1-atm9rezvsi4_2x.webp kuibysheva-10-dsc07482_2x.webp kuibysheva-11-dsc09607_2x.webp kuibysheva-12-dsc06480_2x.webp kuibysheva-13-dsc08464_2x.webp kuibysheva-14-dsc07211_2x.webp kuibysheva-2-leqeb1rvzfq_1_2x.webp kuibysheva-3-eugncsbwnqw_2x.webp kuibysheva-4-czajpkykeyu_2x.webp kuibysheva-5-us6a5dglabw_2x.webp kuibysheva-6-zbnxk11u9ym_2x.webp kuibysheva-7-kjke1fyxlrm_2x.webp kuibysheva-8-f02_zeygjt0_2x.webp kuibysheva-9-dsc09428_2x.webp""",
    "video": """club-heroes6d.mp4""",
}
HTACCESS = r"""DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/css text/javascript application/javascript application/json image/svg+xml
</IfModule>

<IfModule mod_headers.c>
  Header set X-Robots-Tag "noindex, nofollow, noarchive"
  <FilesMatch "\.(html|css|js|json)$">
    Header set Cache-Control "no-cache"
  </FilesMatch>
  <FilesMatch "\.(png|jpe?g|webp|woff2|ttf|mp4)$">
    Header set Cache-Control "public, max-age=604800"
  </FilesMatch>
</IfModule>
"""

def fetch(path: str) -> bytes:
    url = SRC + ("/" if path == "index.html" else "/" + quote(path, safe="/"))
    error = None
    for attempt in range(4):
        try:
            req = Request(url, headers={"User-Agent": "LineaSportaSiteMigration/1.0"})
            with urlopen(req, timeout=50) as res:
                if res.status != 200:
                    raise RuntimeError(f"Unexpected source HTTP {res.status}: {path}")
                return res.read()
        except Exception as exc:
            error = exc
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed source asset {path}: {error}")

def normalized(path: str, raw: bytes) -> bytes:
    if not path.endswith((".html", ".css", ".xml", ".txt")):
        return raw
    text = raw.decode("utf-8")
    text = text.replace(SRC, DEST)
    if path.endswith(".html"):
        text, _ = re.subn(
            r"<script>\(function\(\)\{function c\(\).*?</script>(?=</body></html>)",
            "", text, flags=re.S
        )
        if "/cdn-cgi/challenge-platform" in text:
            raise RuntimeError(f"Cloudflare script remained in {path}")
        if '<meta name="robots"' not in text:
            if "</title>" not in text:
                raise RuntimeError(f"Missing page title: {path}")
            text = text.replace("</title>", '</title><meta name="robots" content="noindex,nofollow,noarchive">', 1)
        text = text.replace(
            'font-4.ttf" as="font" type="font/ttf"',
            'font-4.woff2" as="font" type="font/woff2"'
        )
    elif path == "assets/fonts/fonts.css":
        text = re.sub(
            r"url\(/assets/fonts/font-(\d+)\.ttf\) format\('truetype'\)",
            r"url(/assets/fonts/font-\1.woff2) format('woff2')",
            text
        )
    elif path == "robots.txt":
        text = text.replace("Allow: /", "Disallow: /")
    if SRC in text:
        raise RuntimeError(f"Unconverted preview host in {path}")
    return text.encode("utf-8")

def convert_font(index: int) -> bytes:
    from fontTools.ttLib import TTFont
    raw = fetch(f"assets/fonts/font-{index}.ttf")
    font = TTFont(BytesIO(raw))
    font.flavor = "woff2"
    out = BytesIO()
    font.save(out)
    data = out.getvalue()
    if not data.startswith(b"wOF2") or len(data) < 10000:
        raise RuntimeError(f"Unable to convert font {index} to WOFF2")
    return data

def get_one(path: str) -> tuple[str, bytes]:
    if path in GENERATED_FONTS:
        return path, convert_font(int(path.split("font-")[1].split(".")[0]))
    return path, normalized(path, fetch(path))

def main() -> None:
    if ROOT.exists() and any(
        p.is_file() and p.relative_to(ROOT).as_posix() != "README.md"
        for p in ROOT.rglob("*")
    ):
        raise RuntimeError("new-site already has deployed content; refusing to overwrite")
    sitemap = fetch("sitemap.xml").decode("utf-8")
    locs = ET.fromstring(sitemap).findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    if len(locs) != 30:
        raise RuntimeError(f"Unexpected sitemap route count: {len(locs)}")
    html = set()
    for node in locs:
        url = urlparse(node.text or "")
        if url.netloc != urlparse(SRC).netloc or not url.path.endswith("/"):
            raise RuntimeError("Unexpected sitemap URL: " + (node.text or ""))
        html.add("index.html" if url.path == "/" else url.path.lstrip("/") + "index.html")
    html.update({"404.html", "404/index.html"})
    assets = {f"assets/{group}/{name}" for group, names in GROUPS.items() for name in names.split()}
    assets.add("assets/content.js")
    files = sorted(html | assets | {"app.js", "styles.css", "robots.txt", "sitemap.xml"})
    if len(html) != 32 or len(assets) != 94 or len(files) != 130:
        raise RuntimeError(f"Unexpected manifest: pages={len(html)} assets={len(assets)} files={len(files)}")
    for path in files:
        if str(PurePosixPath(path)) != path or path.startswith("/") or ".." in PurePosixPath(path).parts:
            raise RuntimeError("Unsafe path: " + path)
    completed = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(get_one, path): path for path in files}
        for future in as_completed(futures):
            path, data = future.result()
            completed[path] = data
    completed[".htaccess"] = HTACCESS.encode("utf-8")
    if len(completed) != 131:
        raise RuntimeError("Incomplete site asset count")
    # The approved ZIP fingerprint covers ALL 126 files excluding five regenerated webfont binaries.
    digest = sha256()
    for path in sorted(completed):
        if path in GENERATED_FONTS:
            continue
        digest.update(path.encode("utf-8") + b"\x00" + sha256(completed[path]).digest())
    actual = digest.hexdigest()
    print("Approved source fingerprint:", actual)
    if actual != EXPECTED_HASH:
        raise RuntimeError("Source differs from approved archive. Nothing staged or published.")
    # Only after all assets have passed verification, materialize the site.
    for path, data in completed.items():
        destination = ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    print(f"PASS: {len(html)} HTML pages, {len(assets)} assets, 131 total site files.")
    print("Five WOFF2 files regenerated from unchanged public TTF fonts; no remote FTP writes.")

if __name__ == "__main__":
    main()
