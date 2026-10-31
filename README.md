# Kronika ZPiT Suszanie – wersja na telefon

Strona sama pobiera kronikę z Google Docs co 30 minut i się przebudowuje
(GitHub Actions → GitHub Pages). Wystarczy pisać kronikę w Google Docs jak dotąd.

- Nowy rozdział = nagłówek (styl „Nagłówek 1”) albo pogrubiona pierwsza linijka akapitu, np. **12.11 – Bal w Suchej**
- Nowy rok = linijka „Kronika Zespołu Pieśni i Tańca Suszanie 2027”
- Natychmiastowa aktualizacja: zakładka *Actions* → *Aktualizuj kronikę* → *Run workflow*

Lokalnie: `pip install beautifulsoup4 pillow && python build.py` → strona w `site/`.

## Zdjęcia – tryb kronikarza
5× stuknij logo (albo dodaj `?edytuj` do adresu) → hasło → klikasz zdjęcie → *Przenieś do…*, *Ukryj* albo *Przywróć*.
Zmiany zapisują się w `photos.json` (id zdjęcia → „rok|tytuł wpisu” albo „hidden”) i są u wszystkich po ok. 2 min.
Przy pierwszym zapisie strona poprosi o token GitHuba (Contents: read/write tylko dla tego repo) – zostaje tylko w tym telefonie.
