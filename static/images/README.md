# Grafiki / Images

Umieść tutaj pliki graficzne dla aplikacji.

## Logo

Dodaj plik logo jako:
- `logo.png` - główne logo (będzie wyświetlane obok tytułu w headerze)

**Jak dodać logo:**
1. Zapisz plik jako `logo.png` w folderze `static/images/`
2. Logo automatycznie pojawi się obok tytułu "Turniej Karate" w headerze
3. Jeśli logo nie istnieje, będzie automatycznie ukryte (nie pojawi się błąd)

**Uwagi:**
- **Domyślnie**: Logo jest wyświetlane jako **białe** na czerwonym tle (CSS automatycznie konwertuje)
- Działa dobrze dla:
  - Czarnego logo (np. kaligrafia japońska) → zostanie wyświetlone jako białe
  - Kolorowego logo → zostanie wyświetlone jako białe
- **Jeśli chcesz oryginalne kolory logo** (bez konwersji na białe):
  - Otwórz `templates/base.html`
  - Znajdź linię z `<img src="/static/images/logo.png" ...`
  - Dodaj klasę `logo-dark`: `<img src="/static/images/logo.png" class="logo logo-dark" ...`
- Zalecane rozmiary: 48x48px do 80x80px (CSS automatycznie skaluje do wysokości 48px)
- Format: PNG (z przezroczystością) lub SVG (najlepsze dla skalowania)

## Inne grafiki

- `background.jpg` - tło strony (jeśli potrzebne w przyszłości)
- `favicon.ico` - ikona w karcie przeglądarki

