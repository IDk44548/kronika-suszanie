# Kronika ZPiT Suszanie – wersja na telefon

Strona sama pobiera kronikę z Google Docs co 30 minut i się przebudowuje
(GitHub Actions → GitHub Pages). Wystarczy pisać kronikę w Google Docs jak dotąd.

- Nowy rozdział = nagłówek (styl „Nagłówek 1”) albo pogrubiona pierwsza linijka akapitu, np. **12.11 – Bal w Suchej**
- Nowy rok = linijka „Kronika Zespołu Pieśni i Tańca Suszanie 2027”
- Natychmiastowa aktualizacja: zakładka *Actions* → *Aktualizuj kronikę* → *Run workflow*

Lokalnie: `pip install beautifulsoup4 pillow && python build.py` → strona w `site/`.
