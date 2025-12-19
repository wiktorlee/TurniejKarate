# Plan Minietapów - Rozwój Systemu Turnieju Karate

## ETAP 1: Więcej użytkowników

**Problem:** Obecnie ~25 kukiełek, potrzeba więcej dla lepszej symulacji

**Potrzeba:** 
- Rozszerzyć skrypt o 50-100 kukiełek
- Dodać różnorodność krajów, klubów, kategorii (sex, birth_date, weight)
- Zróżnicować auto_discipline (Kata, Kumite, Both)
- Zróżnicować auto_events_count (NULL, 1, 2, 3...)

**Pliki:** `CREATE_DUMMY_ATHLETES_AUTO.sql` (nowy skrypt)

---

## ETAP 2: Historia zawodów Kata

**Problem:** Lista zawodników nie pokazuje miejsc i punktów po symulacji

**Potrzeba:**
- Sprawdzić czy tabela `results` ma kolumny `place` i `points` (dodać jeśli brakuje)
- Zaktualizować widok `v_kata_competitors` aby zawierał place i points
- Zmodyfikować `kata_competitors()` w `routes/registration.py` - sortować według miejsca
- Zmodyfikować `templates/kata_competitors.html` - dodać kolumny "Miejsce" i "Punkty", pokazać "Brak wyniku" jeśli brak

**Pliki:** 
- SQL: skrypt rozszerzający `results` (jeśli potrzeba)
- SQL: modyfikacja widoku `v_kata_competitors`
- `routes/registration.py` (funkcja `kata_competitors`)
- `templates/kata_competitors.html`

---

## ETAP 3: Historia zawodów Kumite - Zapisywanie wyników

**Problem:** Tabela `draw_fight` nie przechowuje wyników walk (kto wygrał, wyniki)

**Potrzeba:**
- Dodać kolumny do `draw_fight`: `winner_code`, `red_score`, `blue_score`, `round`, `next_fight_id`, `is_finished`
- Dodać foreign key dla `next_fight_id` (self-reference)
- Zaktualizować widok `v_kumite_fights` aby zawierał wyniki
- Zaktualizować `_generate_kumite_bracket()` aby ustawiała `round = 1` dla nowych walk

**Pliki:**
- SQL: skrypt `EXTEND_DRAW_FIGHT_TABLE.sql`
- SQL: modyfikacja widoku `v_kumite_fights`
- `routes/registration.py` (funkcja `_generate_kumite_bracket`)

---

## ETAP 4: Historia zawodów Kumite - Wyświetlanie przebiegu

**Problem:** Drzewka Kumite nie pokazują wyników i wszystkich rund

**Potrzeba:**
- Zmodyfikować `kumite_bracket()` w `routes/registration.py` - pobierać wszystkie rundy, grupować według rundy
- Zmodyfikować `templates/kumite_bracket.html` - pokazać wszystkie rundy, wyniki walk, zwycięzcę każdej walki, "W toku" dla walk bez wyniku, "BYE" dla wolnych losów

**Pliki:**
- `routes/registration.py` (funkcja `kumite_bracket`)
- `templates/kumite_bracket.html`

---

## ETAP 5: Rozszerzenie symulacji - Kata

**Problem:** Procedura `simulate_competitions()` nie generuje wyników Kata

**Potrzeba:**
- Dla każdej kategorii Kata w każdym evencie:
  - Pobrać listę zarejestrowanych zawodników
  - Losowo przypisać miejsca (1, 2, 3, 4...)
  - Obliczyć punkty: 1 miejsce = 10 pkt, 2 = 7 pkt, 3 = 5 pkt, 4 = 3 pkt, 5+ = 1 pkt
  - Wstawić wyniki do tabeli `results` (athlete_code, event_id, category_kata_id, place, points, discipline_id)

**Pliki:**
- SQL: modyfikacja procedury `simulate_competitions()` w Supabase
- Dokumentacja: `SQL_ETAP_ADMIN_DOKUMENTACJA.md`

---

## ETAP 6: Rozszerzenie symulacji - Kumite

**Problem:** Procedura `simulate_competitions()` nie generuje przebiegu walk (tylko runda 1)

**Potrzeba:**
- Dla każdej kategorii Kumite w każdym evencie:
  - Pobrać drzewko walk z `draw_fight` (runda 1)
  - Dla każdej walki w rundzie 1: losowo wybrać zwycięzcę, wygenerować wynik, zaktualizować `draw_fight`
  - Dla kolejnych rund: utworzyć nowe pary (zwycięzcy z poprzedniej rundy), obsłużyć BYE jeśli nieparzysta liczba, wygenerować wyniki, powtarzać aż zostanie 1 zwycięzca
  - Przypisać miejsca: zwycięzca = 1, finalista = 2, półfinaliści = 3
  - Wstawić wyniki do tabeli `results`

**Pliki:**
- SQL: modyfikacja procedury `simulate_competitions()` w Supabase
- Dokumentacja: `SQL_ETAP_ADMIN_DOKUMENTACJA.md`

---

## ETAP 7: Rozszerzenie widoku "Moje zgłoszenie"

**Problem:** Widok nie pokazuje miejsc i punktów po symulacji

**Potrzeba:**
- Zmodyfikować `my_registration()` w `routes/registration.py` - pobierać wyniki z tabeli `results` dla każdej rejestracji
- Zmodyfikować `templates/my_registration.html` - dodać sekcję z wynikami (dla Kata: "Miejsce: X, Punkty: Y", dla Kumite: "Miejsce: X"), pokazać "Brak wyniku" dla zawodów bez symulacji

**Pliki:**
- `routes/registration.py` (funkcja `my_registration`)
- `templates/my_registration.html`



