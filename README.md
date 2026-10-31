# Kronika ZPiT Suszanie – wersja na telefon

Strona sama pobiera kronikę z Google Docs co 30 minut i się przebudowuje
(GitHub Actions → GitHub Pages). Wystarczy pisać kronikę w Google Docs jak dotąd.

- Nowy rozdział = nagłówek (styl „Nagłówek 1”) albo pogrubiona pierwsza linijka akapitu, np. **12.11 – Bal w Suchej**
- Nowy rok = linijka „Kronika Zespołu Pieśni i Tańca Suszanie 2027”
- Natychmiastowa aktualizacja: zakładka *Actions* → *Aktualizuj kronikę* → *Run workflow*

Lokalnie: `pip install beautifulsoup4 pillow && python build.py` → strona w `site/`.

## Tryb kronikarza
5× stuknij logo (albo dodaj `?edytuj` do adresu) → hasło → potem:
- **zdjęcie** → *Przenieś do…*, *Ukryj*, *Przywróć*,
- **osoba w składzie** → popraw / usuń; *+ Dodaj osobę*,
- **+ Nowy wpis** → rok, data, tytuł, tekst, miejsce w kronice i zdjęcia wybrane z kroniki; wpis można potem edytować i usunąć.
- **✎ Edytuj wpis** na każdej karcie – także wpisy z Google Docs: tytuł, data, tekst, zdjęcia, ukrycie wpisu, „Przywróć wersję z dokumentu”.

Zmiany zapisują się w `photos.json` (Google Doc zostaje nietknięty) i są u wszystkich po ok. 2 min.
Przy pierwszym zapisie strona poprosi o token GitHuba (Contents: read/write tylko dla tego repo) – zostaje tylko w tym telefonie.
