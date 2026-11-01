#!/usr/bin/env bash
# Wysyła nowe zdjęcia i filmy z folderu wideo/ na stronę (trafiają do wydarzenia „Foto”).
# Duże zdjęcia zmniejsza do 2400 px, filmy przygotowuje do szybkiego startu (faststart) i nadaje proste nazwy.
set -e
cd "$(dirname "$0")"
git pull -q --rebase

new=$(git ls-files --others --exclude-standard wideo)
[ -z "$new" ] && { echo "Brak nowych plików w wideo/"; exit 0; }
echo "$new"

git ls-files --others --exclude-standard -z wideo | python -X utf8 -c "
import os, re, subprocess, sys
from PIL import Image, ImageOps
for f in sys.stdin.read().split('\0'):
    low = f.lower()
    if low.endswith(('.jpg', '.jpeg', '.png')) and os.path.getsize(f) > 1_500_000:
        im = ImageOps.exif_transpose(Image.open(f)).convert('RGB'); im.thumbnail((2400, 2400))
        im.save(f, 'JPEG', quality=88, optimize=True, progressive=True)
    elif low.endswith(('.mp4', '.mov', '.m4v')):
        stem = re.sub(r'[^a-z0-9]+', '-', os.path.splitext(os.path.basename(f))[0].lower()).strip('-') or 'film'
        out = os.path.join('wideo', stem + '.mp4')
        tmp = out + '.tmp.mp4'
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f, '-c', 'copy', '-movflags', '+faststart', tmp], check=True)
        os.remove(f); os.replace(tmp, out)
"
git add wideo
git commit -q -m "Nowe zdjęcia i filmy w „Foto”

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
# kronikarz może w tym czasie zapisywać zmiany z telefonu – wtedy dociągamy i ponawiamy
for i in 1 2 3 4 5; do git pull -q --rebase && git push -q && break; sleep 3; done
echo "Wysłane. Czekam na stronę…"
check=$(git log -1 --name-only --format= | grep '^wideo/' | head -1)
name=$(basename "$check"); key=$(echo "${name%.*}" | sed 's/[^A-Za-z0-9_-]\+/-/g' | cut -c1-40)
until curl -s "https://idk44548.github.io/kronika-suszanie/?x=$RANDOM" | grep -q -- "$key"; do sleep 15; done
echo "Na stronie."
