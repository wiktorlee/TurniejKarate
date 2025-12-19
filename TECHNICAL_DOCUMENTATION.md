# Dokumentacja Techniczna - System Turnieju Karate

## Baza Danych

### Tabele (11)
| Tabela | Opis |
|--------|------|
| `users` | zawodnicy/użytkownicy (athlete_code, login, country_code) |
| `events` | zawody/turnieje |
| `clubs` | kluby karate |
| `categories_kata` | kategorie Kata (wiek, płeć) |
| `categories_kumite` | kategorie Kumite (wiek, płeć, waga) |
| `registrations` | zgłoszenia zawodników na eventy |
| `draw_fight` | drzewko walk Kumite (pary zawodników) |
| `results` | wyniki i punkty zawodników |
| `disciplines` | dyscypliny (Kata, Kumite) |
| `categories` | (legacy, nieużywane) |
| `athlete_code_counter` | pomocnicza do generowania kodów |

### Klucze Obce
| Tabela źródłowa | Kolumna | Tabela docelowa | Kolumna |
|-----------------|---------|-----------------|---------|
| `registrations` | `athlete_code` | `users` | `athlete_code` |
| `registrations` | `event_id` | `events` | `id` |
| `registrations` | `category_kata_id` | `categories_kata` | `id` |
| `registrations` | `category_kumite_id` | `categories_kumite` | `id` |
| `draw_fight` | `red_code`, `blue_code` | `users` | `athlete_code` |
| `draw_fight` | `category_kumite_id` | `categories_kumite` | `id` |
| `results` | `athlete_code` | `users` | `athlete_code` |
| `results` | `event_id` | `events` | `id` |
| `users` | `club_name` | `clubs` | `name` |

### Constraints
- **CHECK:** `sex IN ('M', 'F')`, `weight > 0`, `points >= 0`, `country_code = 3 znaki`
- **UNIQUE:** `users.login`, `users.athlete_code`, `clubs.name`

---

## Widoki SQL (5)

| Widok | Opis | Gdzie używany |
|-------|------|---------------|
| `v_kata_competitors` | Lista zawodników Kata z danymi eventu/kategorii | `routes/registration.py` |
| `v_kumite_competitors` | Lista zawodników Kumite z danymi eventu/kategorii | `routes/registration.py` |
| `v_user_registrations` | Rejestracje użytkownika z pełnymi danymi | `routes/registration.py` |
| `v_kumite_fights` | Pojedynki Kumite z danymi zawodników (red/blue) | `routes/registration.py` |
| `v_results_with_users` | Wyniki z danymi zawodników | `routes/rankings.py` |

---

## Triggery i Funkcje SQL

| Element | Tabela/Trigger | Co robi | Gdzie w kodzie |
|---------|----------------|---------|----------------|
| **Trigger** | `trg_users_set_code` | BEFORE INSERT na `users`, generuje `athlete_code` (POL001...) | `routes/auth.py` (automatycznie) |
| **Funkcja SQL** | `generate_athlete_code()` | Generuje kod zawodnika | Wywoływana przez trigger |

---

## Podział Funkcjonalności: SQL vs Backend

### Po stronie SQL (Baza Danych)

| Element | Co robi | Przykład |
|---------|---------|----------|
| **Funkcje SQL (stored functions)** | Logika generowania danych, obliczenia | `generate_athlete_code()` - generuje kod zawodnika |
| **Triggery** | Automatyczne akcje przy zmianach danych | `trg_users_set_code` - automatycznie generuje `athlete_code` przy INSERT |
| **Widoki SQL** | Predefiniowane zapytania z JOIN-ami | `v_user_registrations`, `v_kata_competitors` - upraszczają SELECT-y |
| **Constraints (CHECK)** | Walidacja danych na poziomie bazy | `sex IN ('M', 'F')`, `points >= 0`, `weight > 0` |
| **Foreign Keys** | Integralność referencyjna | Automatyczna walidacja relacji między tabelami |
| **UNIQUE constraints** | Zapewnienie unikalności | `users.login`, `users.athlete_code` |

**Gdzie:** W bazie danych (PostgreSQL/Supabase SQL Editor)

### Po stronie Backend (Python)

| Element | Co robi | Przykład |
|---------|---------|----------|
| **Walidacja biznesowa** | Sprawdzanie reguł biznesowych | Wiek zawodnika, dopasowanie do kategorii (`routes/categories.py`) |
| **Transakcje** | Zarządzanie atomowością operacji | `BEGIN`/`COMMIT`/`ROLLBACK` w `routes/categories.py:141` |
| **Wykonywanie zapytań SQL** | Wysyłanie zapytań do bazy | `cur.execute()` - wszystkie zapytania przez Python |
| **Formatowanie danych** | Przygotowanie danych do wyświetlenia | Przetwarzanie wyników z bazy dla szablonów Jinja2 |
| **Logika aplikacji** | Przepływ działania aplikacji | Routing, sesje, autoryzacja (Flask blueprints) |
| **Obsługa błędów** | Zarządzanie wyjątkami | `try/except` bloki, `flash()` messages |

**Gdzie:** W kodzie Python (`routes/*.py`, `app.py`)

### Współpraca SQL ↔ Backend

| Operacja | SQL | Backend |
|----------|-----|---------|
| **Generowanie kodu zawodnika** | Funkcja `generate_athlete_code()` + trigger | Python wykonuje `INSERT INTO users`, trigger automatycznie generuje kod |
| **Pobieranie listy zawodników** | Widok `v_kata_competitors` (JOIN-y w bazie) | Python wykonuje `SELECT * FROM v_kata_competitors` |
| **Rejestracja na zawody** | Constraints (FOREIGN KEY, CHECK) walidują dane | Python waliduje wiek/wagę, zarządza transakcją |
| **Rankingi** | Widok `v_results_with_users` (JOIN `results` + `users`) | Python wykonuje `SELECT` z GROUP BY, formatuje wyniki |
| **Wycofanie dyscypliny** | Constraints zapewniają integralność | Python zarządza transakcją (UPDATE/DELETE) |

**Podsumowanie:**
- **SQL:** Przechowywanie danych, automatyczna walidacja, generowanie danych, złożone JOIN-y (widoki)
- **Backend:** Logika biznesowa, walidacja reguł, zarządzanie transakcjami, formatowanie, routing

---

## Transakcje (3)

| Operacja | Plik | Linia | Co robi |
|----------|------|-------|---------|
| Rejestracja na obie dyscypliny | `routes/categories.py` | 141 | 2x INSERT do `registrations` (Kata + Kumite) |
| Wycofanie dyscypliny | `routes/registration.py` | 139 | UPDATE/DELETE w `registrations` |
| Generowanie drzewka walk | `routes/registration.py` | 375 | Wielokrotne INSERT-y do `draw_fight` |

**Wzorzec:** `BEGIN` → operacje SQL → `COMMIT` / `ROLLBACK`

---

## Struktura Kodu Python

| Plik | Opis |
|------|------|
| `app.py` | rejestracja blueprintów, konfiguracja Flask |
| `database.py` | połączenie z bazą (`get_conn()`) |
| `config.py` | konfiguracja (`SCHEMA = "karate"`, `DB_URL`) |
| `routes/auth.py` | logowanie, rejestracja (używa triggera) |
| `routes/profile.py` | profil użytkownika, edycja danych |
| `routes/categories.py` | wybór kategorii, rejestracja na zawody (transakcja) |
| `routes/registration.py` | lista zawodników, drzewko walk, wycofanie (widoki + transakcje) |
| `routes/rankings.py` | rankingi (widok `v_results_with_users`) |
| `routes/main.py` | strona główna, health check |

---

## Gdzie Szukać w Kodzie

| Funkcjonalność | Plik | Funkcja | Tabela/Widok | Transakcja |
|----------------|------|---------|--------------|------------|
| Rejestracja na zawody | `routes/categories.py` | `categories()` | `registrations` | Tak (2 dyscypliny) |
| Lista zawodników Kata | `routes/registration.py` | `kata_competitors()` | `v_kata_competitors` | Nie |
| Drzewko walk Kumite | `routes/registration.py` | `kumite_bracket()` | `v_kumite_fights`, `draw_fight` | Tak |
| Rankingi | `routes/rankings.py` | `show_rankings()` | `v_results_with_users` | Nie |
| Generowanie kodu | `routes/auth.py` | `register()` | Trigger `trg_users_set_code` | Nie |
| Wycofanie dyscypliny | `routes/registration.py` | `withdraw_discipline()` | `registrations` | Tak |

---

## Kluczowe Koncepcje

| Koncepcja | Opis |
|----------|------|
| **FOREIGN KEY** | Integralność referencyjna (np. `results.athlete_code` → `users.athlete_code`) |
| **CHECK Constraints** | Walidacja na poziomie bazy (`sex IN ('M', 'F')`, `points >= 0`) |
| **Widoki** | JOIN-y w bazie, prosty SELECT w Pythonie |
| **Transakcje** | Atomowość operacji (wszystko lub nic) dla operacji wieloetapowych |
| **Trigger** | Automatyczne akcje przy INSERT/UPDATE/DELETE (generowanie `athlete_code`) |
| **Funkcje SQL** | W bazie danych, wywoływane przez triggery lub bezpośrednio |

---

## Szybkie Odniesienia

| Element | Lokalizacja w kodzie | Lokalizacja w bazie |
|---------|---------------------|---------------------|
| Widoki | `routes/registration.py`, `routes/rankings.py` | `karate.v_*` |
| Transakcje | `routes/categories.py:141`, `routes/registration.py:139,375` | - |
| Trigger | `routes/auth.py` (użycie) | `karate.trg_users_set_code` |
| Funkcje SQL | - | `karate.generate_athlete_code()` |
| Foreign Keys | Wszędzie (automatyczna walidacja) | Constraints w tabelach |
| JOIN-y | W widokach SQL | `karate.v_*` |

---

*Dokumentacja zwięzła - 2025-01-09*
