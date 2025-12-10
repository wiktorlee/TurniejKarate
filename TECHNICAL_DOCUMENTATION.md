# Dokumentacja Techniczna - System Turnieju Karate

## Struktura Bazy Danych

### Tabele (11)
- **`users`** - zawodnicy/użytkownicy (athlete_code, login, country_code)
- **`events`** - zawody/turnieje
- **`clubs`** - kluby karate
- **`categories_kata`** - kategorie Kata (wiek, płeć)
- **`categories_kumite`** - kategorie Kumite (wiek, płeć, waga)
- **`registrations`** - zgłoszenia zawodników na eventy
- **`draw_fight`** - drzewko walk Kumite (pary zawodników)
- **`results`** - wyniki i punkty zawodników
- **`disciplines`** - dyscypliny (Kata, Kumite)
- **`categories`** - (legacy, nieużywane)
- **`athlete_code_counter`** - pomocnicza do generowania kodów

### Klucze Obce (FOREIGN KEY)
```
users.athlete_code ←── registrations.athlete_code
users.athlete_code ←── draw_fight.red_code, blue_code
users.athlete_code ←── results.athlete_code
events.id ←── registrations.event_id
events.id ←── results.event_id
categories_kata.id ←── registrations.category_kata_id
categories_kumite.id ←── registrations.category_kumite_id
categories_kumite.id ←── draw_fight.category_kumite_id
clubs.name ←── users.club_name
disciplines.id ←── registrations.discipline_id
```

### Constraints
- **CHECK:** `sex IN ('M', 'F')`, `weight > 0`, `points >= 0`, `country_code = 3 znaki`
- **UNIQUE:** `users.login`, `users.athlete_code`, `clubs.name`
- **FOREIGN KEY:** wszystkie powyższe relacje

---

## Widoki SQL (5)

### 1. `v_kata_competitors`
**Co robi:** Lista zawodników Kata z danymi eventu i kategorii  
**Gdzie w kodzie:** `routes/registration.py`:
- Linia 197: info o evencie/kategorii
- Linia 212: lista zawodników

### 2. `v_kumite_competitors`
**Co robi:** Lista zawodników Kumite z danymi eventu i kategorii  
**Gdzie w kodzie:** `routes/registration.py`:
- Linia 266: info o evencie/kategorii
- Linia 349: lista zawodników (generowanie drzewka)

### 3. `v_user_registrations`
**Co robi:** Rejestracje użytkownika z pełnymi danymi eventów/kategorii  
**Gdzie w kodzie:** `routes/registration.py`, linia 30 (`my_registration()`)

### 4. `v_kumite_fights`
**Co robi:** Pojedynki Kumite z danymi obu zawodników (red/blue)  
**Gdzie w kodzie:** `routes/registration.py`, linia 301 (`kumite_bracket()`)

### 5. `v_results_with_users`
**Co robi:** Wyniki z danymi zawodników (imię, nazwisko, klub, kraj)  
**Gdzie w kodzie:** `routes/rankings.py`:
- Linia 21: ranking klubowy
- Linia 33: ranking narodowościowy
- Linia 48: ranking indywidualny

**Dlaczego widoki:** Zastępują JOIN-y w Pythonie, upraszczają kod, łatwiejsze utrzymanie.

---

## Triggery (1)

### `trg_users_set_code`
**Tabela:** `users`  
**Kiedy:** BEFORE INSERT  
**Co robi:** Automatycznie generuje `athlete_code` (np. POL001, POL002)  
**Jak:** Używa `athlete_code_counter` do liczenia  
**Gdzie w kodzie:** `routes/auth.py` - rejestracja użytkownika (automatycznie)

---

## Transakcje (3)

### 1. Rejestracja na obie dyscypliny
**Plik:** `routes/categories.py`, linia 141  
**Operacje:** 2x INSERT do `registrations` (Kata + Kumite)  
**Dlaczego:** Jeśli drugi INSERT się nie powiedzie, pierwszy jest cofany (spójność danych)

### 2. Wycofanie dyscypliny
**Plik:** `routes/registration.py`, linia 139  
**Operacje:** UPDATE/DELETE w `registrations`  
**Dlaczego:** Zapewnia atomowość operacji (wszystko lub nic)

### 3. Generowanie drzewka walk
**Plik:** `routes/registration.py`, linia 375 (`_generate_kumite_bracket()`)  
**Operacje:** Wielokrotne INSERT-y do `draw_fight` (w pętli)  
**Dlaczego:** Wszystkie pojedynki zapisują się razem lub żaden (kompletne drzewko)

**Wzorzec transakcji:**
```python
try:
    conn.execute("BEGIN")
    # operacje SQL
    conn.commit()
except Exception as e:
    conn.rollback()
    # obsługa błędu
```

---

## Struktura Kodu Python

### Pliki główne
- **`app.py`** - rejestracja blueprintów, konfiguracja Flask
- **`database.py`** - połączenie z bazą (`get_conn()`)
- **`config.py`** - konfiguracja (`SCHEMA = "karate"`, `DB_URL`)

### Routes (blueprinty)
- **`routes/auth.py`** - logowanie, rejestracja (używa triggera do kodów)
- **`routes/profile.py`** - profil użytkownika, edycja danych
- **`routes/categories.py`** - wybór kategorii, rejestracja na zawody (transakcja!)
- **`routes/registration.py`** - lista zawodników, drzewko walk, wycofanie (widoki + transakcje)
- **`routes/rankings.py`** - rankingi klubowy, narodowościowy, indywidualny (widok `v_results_with_users`)
- **`routes/main.py`** - strona główna, health check

### Templates
- **`templates/base.html`** - szablon bazowy (menu nawigacyjne)
- **`templates/rankings.html`** - wyświetlanie rankingów
- **`templates/kata_competitors.html`** - lista zawodników Kata
- **`templates/kumite_bracket.html`** - drzewko walk Kumite
- **`templates/my_registration.html`** - moje zgłoszenia

---

## Gdzie Szukać w Kodzie

### Rejestracja zawodnika na zawody
**Plik:** `routes/categories.py`, funkcja `categories()`  
**Tabela:** `registrations`  
**Transakcja:** Tak (linia 141) - jeśli obie dyscypliny

### Lista zawodników Kata
**Plik:** `routes/registration.py`, funkcja `kata_competitors()`  
**Widok:** `v_kata_competitors`  
**Template:** `templates/kata_competitors.html`

### Drzewko walk Kumite
**Plik:** `routes/registration.py`, funkcja `kumite_bracket()`  
**Widok:** `v_kumite_fights` (wyświetlanie), `v_kumite_competitors` (generowanie)  
**Tabela:** `draw_fight`  
**Transakcja:** Tak (linia 375) - przy generowaniu

### Rankingi
**Plik:** `routes/rankings.py`, funkcja `show_rankings()`  
**Widok:** `v_results_with_users`  
**Tabela:** `results`  
**Template:** `templates/rankings.html`

### Generowanie kodu zawodnika
**Plik:** `routes/auth.py`, funkcja `register()`  
**Trigger:** `trg_users_set_code` (automatycznie w bazie)

### Wycofanie z dyscypliny
**Plik:** `routes/registration.py`, funkcja `withdraw_discipline()`  
**Tabela:** `registrations`  
**Transakcja:** Tak (linia 139)

---

## Łączenie Tabel (JOIN)

### W widokach SQL (zalecane)
- `v_kata_competitors`: `registrations` JOIN `users` JOIN `events` JOIN `categories_kata`
- `v_kumite_competitors`: `registrations` JOIN `users` JOIN `events` JOIN `categories_kumite`
- `v_user_registrations`: `registrations` LEFT JOIN `events`, `categories_kata`, `categories_kumite`
- `v_kumite_fights`: `draw_fight` LEFT JOIN `users` (2x - red i blue)
- `v_results_with_users`: `results` JOIN `users`

### W kodzie Python (proste przypadki)
- Bezpośrednie SELECT-y bez JOIN-ów (gdy nie ma widoku)
- Wszystkie zapytania używają parametrów `%s` (ochrona przed SQL injection)

---

## Kluczowe Koncepcje

### FOREIGN KEY
**Cel:** Zapewnia integralność referencyjną  
**Przykład:** Nie można dodać wyniku dla nieistniejącego zawodnika (`results.athlete_code` → `users.athlete_code`)

### CHECK Constraints
**Cel:** Walidacja danych na poziomie bazy  
**Przykłady:** `sex IN ('M', 'F')`, `points >= 0`, `weight > 0`

### Widoki vs JOIN-y w Pythonie
- **Widoki:** Logika JOIN-ów w bazie, prosty SELECT w Pythonie
- **Korzyści:** Reużywalność, łatwiejsze utrzymanie, spójność

### Transakcje
**Cel:** Atomowość operacji (wszystko lub nic)  
**Gdzie:** Operacje wieloetapowe (2+ INSERT-y, UPDATE + DELETE)

### Trigger
**Cel:** Automatyczne akcje przy INSERT/UPDATE/DELETE  
**Przykład:** Generowanie `athlete_code` przy rejestracji użytkownika

---

## Szybkie Odniesienia

| Element | Lokalizacja w kodzie | Lokalizacja w bazie |
|---------|---------------------|---------------------|
| Widoki | `routes/registration.py`, `routes/rankings.py` | `karate.v_*` |
| Transakcje | `routes/categories.py:141`, `routes/registration.py:139,375` | - |
| Trigger | `routes/auth.py` (użycie) | `karate.trg_users_set_code` |
| Foreign Keys | Wszędzie (automatyczna walidacja) | Constraints w tabelach |
| JOIN-y | W widokach SQL | `karate.v_*` |

---

*Dokumentacja zwięzła - 2025-01-09*
