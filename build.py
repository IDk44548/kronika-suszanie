"""Buduje mobilną stronę kroniki ZPiT Suszanie z Google Doca.

Pobiera dokument jako ZIP (HTML + zdjęcia), dzieli go na lata i rozdziały,
zmniejsza zdjęcia i zapisuje gotową stronę do katalogu site/.
Uruchamiane automatycznie przez GitHub Actions (.github/workflows/build.yml).
"""
import hashlib
import html
import io
import json
import urllib.parse
import re
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageOps

DOC_ID = "1-WabgJuRqsgB8YhJ2iRPlvKM6vWO6GXjR6vs1TGm-bc"
ROOT = Path(__file__).parent
OUT = ROOT / "site"
MAX_IMG = 1400

YEAR_RE = re.compile(r"Kronika Zespołu.*?(\d{4})")
DATE_RE = re.compile(r"^\s*((?:\d{1,2}(?:\.\d{1,2})?\s*[-–]\s*)?\d{1,2}\.\d{1,2}(?:\.\d{2,4})?)\s*[-–:]?\s*(.*)$")
SPACES_RE = re.compile(r"[\s ]{3,}")


def download():
    url = f"https://docs.google.com/document/d/{DOC_ID}/export?format=zip"
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    z = zipfile.ZipFile(io.BytesIO(data))
    name = next(n for n in z.namelist() if n.endswith(".html"))
    images = {n.split("/", 1)[1]: z.read(n) for n in z.namelist() if n.startswith("images/") and not n.endswith("/")}
    return z.read(name).decode("utf-8"), images


def style_classes(raw):
    """Klasy CSS Google Docs oznaczające pogrubienie / kursywę."""
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", raw, re.S))
    bold, italic = set(), set()
    for cls, body in re.findall(r"\.(c\d+)\{([^}]*)\}", css):
        if "font-weight:700" in body:
            bold.add(cls)
        if "font-style:italic" in body:
            italic.add(cls)
    return bold, italic


def unwrap_google_link(href):
    m = re.search(r"[?&]q=([^&]+)", href or "")
    if "google.com/url" in (href or "") and m:
        return urllib.parse.unquote(m.group(1))
    return href


class Parser:
    def __init__(self, raw, images):
        self.bold, self.italic = style_classes(raw)
        self.images = images
        self.used_images = []
        self.years = []
        self.cur_year = None
        self.cur_sec = None
        self.soup = BeautifulSoup(raw, "html.parser")

    # --- struktura -------------------------------------------------------
    def new_year(self, year):
        self.cur_year = {"year": year, "members": [], "covers": [], "sections": []}
        self.years.append(self.cur_year)
        self.cur_sec = None

    def new_section(self, title):
        if self.cur_year is None:
            self.new_year("")
        m = DATE_RE.match(title)
        date, name = (m.group(1).replace(" ", ""), m.group(2).strip(" -–")) if m and m.group(2).strip() else ("", title)
        self.cur_sec = {"title": name or title, "date": date, "blocks": []}
        self.cur_year["sections"].append(self.cur_sec)

    def add_block(self, kind, payload):
        if self.cur_year is None:
            self.new_year("")
        if self.cur_sec is None:
            if kind == "img":
                self.cur_year["covers"].append(payload)
                return
            if kind == "text":
                # tekst przed pierwszym rozdziałem roku = skład zespołu
                self.cur_year["members"].extend(self.member_names(payload))
                return
            self.new_section("Wstęp")
        blocks = self.cur_sec["blocks"]
        if kind == "img" and blocks and blocks[-1][0] == "gallery":
            blocks[-1][1].append(payload)
        elif kind == "img":
            blocks.append(["gallery", [payload]])
        else:
            blocks.append([kind, payload])

    def member_names(self, frag_html):
        text = re.sub(r"<br\s*/?>", "\n", frag_html)
        text = html.unescape(re.sub(r"<[^>]+>", "", text))
        names = []
        for line in text.split("\n"):
            for part in SPACES_RE.split(line):
                part = part.strip()
                if not part or part.endswith(":") or part.isupper() or len(part) > 40:
                    continue
                names.append(part)
        return names

    # --- treść -----------------------------------------------------------
    def inline(self, node):
        """Zamienia zawartość akapitu na listę 'linii' (rozdzielonych <br>) z HTML."""
        lines, cur = [], []

        def push(text, bold, italic, href=None):
            if not text:
                return
            t = html.escape(text)
            if href:
                t = f'<a href="{html.escape(href)}" target="_blank" rel="noopener">{t}</a>'
            if italic:
                t = f"<em>{t}</em>"
            cur.append((t, bold, text))

        def walk(n, bold=False, italic=False, href=None):
            for c in n.children:
                if isinstance(c, NavigableString):
                    push(str(c), bold, italic, href)
                elif c.name == "br":
                    lines.append(list(cur))
                    cur.clear()
                elif c.name == "img":
                    self.pending_imgs.append(c.get("src", ""))
                else:
                    cls = set(c.get("class") or [])
                    walk(c, bold or bool(cls & self.bold), italic or bool(cls & self.italic),
                         unwrap_google_link(c.get("href")) if c.name == "a" else href)

        walk(node)
        lines.append(list(cur))
        return lines

    @staticmethod
    def render(runs):
        out, open_b = [], False
        for t, b, _ in runs:
            if b and not open_b:
                out.append("<strong>"); open_b = True
            if not b and open_b:
                out.append("</strong>"); open_b = False
            out.append(t)
        if open_b:
            out.append("</strong>")
        return "".join(out).replace(" ", " ").strip()

    def handle_para(self, el, is_heading):
        self.pending_imgs = []
        lines = self.inline(el)
        plain = "".join(r[2] for line in lines for r in line).replace(" ", " ").strip()

        ym = YEAR_RE.match(plain)
        if ym:
            self.new_year(ym.group(1))
            first = "".join(r[2] for r in lines[0])
            rest_first = first[ym.end():] if first.startswith(plain[: ym.end()]) else ""
            body = [[(html.escape(rest_first), True, rest_first)]] + lines[1:] if rest_first.strip() else lines[1:]
            for line in body:
                txt = self.render(line)
                if txt:
                    self.add_block("text", txt)
        elif is_heading and plain:
            self.new_section(plain)
        elif plain:
            # nagłówek = pogrubiony początek linijki (akapitu albo po <br>), np. „11.01 Bal gminny”
            in_intro = self.cur_year is not None and self.cur_sec is None and not self.cur_year["sections"]
            members = in_intro and self.looks_like_members(lines)
            buf = []

            def flush():
                if buf:
                    self.add_block("text", "<br>".join(buf))
                    buf.clear()

            started = False
            for line in lines:
                if not "".join(r[2] for r in line).replace(" ", " ").strip():
                    if started:
                        flush()
                    continue
                i = 0
                while i < len(line) and (line[i][1] or not line[i][2].strip()):
                    i += 1
                head = "".join(r[2] for r in line[:i]).replace(" ", " ").strip()
                if not started:  # pierwsza linijka akapitu – luźniejsza reguła
                    ok = head and len(head) <= 110 and (i == len(line) or DATE_RE.match(head)
                                                       or (len(head) <= 70 and head[-1] not in ".,!?…:;"))
                else:  # w środku akapitu – tylko data albo cała linijka pogrubiona
                    ok = head and len(head) <= 90 and (DATE_RE.match(head) or (i == len(line) and len(head) <= 70))
                started = True
                if ok and not members:
                    flush()
                    self.new_section(head.rstrip(":").strip())
                    line = line[i:]
                txt = self.render(line)
                if txt:
                    buf.append(txt)
            flush()
        for src in self.pending_imgs:
            name = src.split("/")[-1]
            if name in self.images:
                self.used_images.append(name)
                self.add_block("img", name)

    def looks_like_members(self, lines):
        txt = "".join(r[2] for line in lines for r in line)
        return bool(SPACES_RE.search(txt)) or "tancerze" in txt.lower()

    def parse(self):
        body = self.soup.body
        for el in body.find_all(["p", "h1", "h2", "h3", "h4", "li", "table"]):
            if el.find_parent(["table"]) and el.name != "table":
                continue
            if el.name == "table":
                for cell in el.find_all("td"):
                    self.handle_para(cell, False)
                continue
            self.handle_para(el, el.name.startswith("h") or "subtitle" in (el.get("class") or []) or "title" in (el.get("class") or []))
        return self.years


def save_images(names, images, dest):
    dest.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name in dict.fromkeys(names):
        im = Image.open(io.BytesIO(images[name]))
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.convert("RGBA").split()[-1])
            im = bg
        im.thumbnail((MAX_IMG, MAX_IMG))
        out = Path(name).stem + "-" + hashlib.md5(images[name]).hexdigest()[:8] + ".jpg"
        im.convert("RGB").save(dest / out, "JPEG", quality=82, optimize=True, progressive=True)
        meta[name] = {"src": "img/" + out, "w": im.width, "h": im.height}
    return meta


def main():
    if len(sys.argv) > 1:  # lokalnie: python build.py doc.zip
        z = zipfile.ZipFile(sys.argv[1])
        name = next(n for n in z.namelist() if n.endswith(".html"))
        raw = z.read(name).decode("utf-8")
        images = {n.split("/", 1)[1]: z.read(n) for n in z.namelist() if n.startswith("images/") and not n.endswith("/")}
    else:
        raw, images = download()

    years = Parser(raw, images).parse()
    years = [y for y in years if y["sections"] or y["members"]]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    used = [b for y in years for s in y["sections"] for k, v in s["blocks"] if k == "gallery" for b in v]
    used += [c for y in years for c in y["covers"]]
    meta = save_images(used, images, OUT / "img")
    for y in years:
        y["members"] = list(dict.fromkeys(y["members"]))
        y["covers"] = [meta[n] for n in y["covers"]]
        for s in y["sections"]:
            s["blocks"] = [[k, [meta[n] for n in v] if k == "gallery" else v] for k, v in s["blocks"]]
        y["sections"] = [s for s in y["sections"] if s["blocks"]]

    data = {"years": years, "updated": datetime.now(timezone.utc).isoformat(timespec="minutes")}
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    page = template.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (OUT / "index.html").write_text(page, encoding="utf-8")
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, OUT / f.name)
    (OUT / ".nojekyll").write_text("")
    n_sec = sum(len(y["sections"]) for y in years)
    print(f"OK: {len(years)} lat, {n_sec} rozdziałów, {len(meta)} zdjęć")


if __name__ == "__main__":

    main()
