# Plan: Masowe Tworzenie Kukiełek (Sztucznych Zawodników)

## Cel
Utworzenie zestawu sztucznych kont zawodników, które będą się automatycznie rejestrowały na te same kategorie przy każdym wywołaniu procedury `restore_dummy_athletes_registrations()`.

---

## Założenia

### 1. Kukiełki tworzone RAZ
- Konta są tworzone jednorazowo w bazie danych
- Mają niezmienne parametry: wiek, waga, płeć, kraj, klub, narodowość
- Mają przypisane `auto_category_kata_id` i/lub `auto_category_kumite_id`
- Mają ustawione `auto_discipline` (kata/kumite/both)
- Mają `is_dummy = true`

### 2. Masowa rejestracja WIELOKROTNIE
- Przy każdym kliknięciu "Zarejestruj kukiełki" w panelu admina
- Te same kukiełki rejestrują się na te same kategorie
- Procedura SQL sprawdza duplikaty, więc można wywoływać bezpiecznie

---

## Struktura Skryptu SQL

### ETAP 1: Sprawdzenie istniejących kategorii
```sql
-- Sprawdź jakie kategorie kata istnieją
SELECT id, name, sex, min_age, max_age 
FROM karate.categories_kata 
WHERE is_active = true
ORDER BY sex, min_age;

-- Sprawdź jakie kategorie kumite istnieją
SELECT id, name, sex, min_age, max_age, min_weight, max_weight 
FROM karate.categories_kumite 
WHERE is_active = true
ORDER BY sex, min_age, min_weight;
```

### ETAP 2: Sprawdzenie istniejących klubów i krajów
```sql
-- Sprawdź dostępne kluby
SELECT name FROM karate.clubs ORDER BY name;

-- Sprawdź jakie kody krajów już istnieją
SELECT DISTINCT country_code FROM karate.users ORDER BY country_code;
```

### ETAP 3: Przygotowanie danych kukiełek
Kukiełki powinny być różnorodne:
- Różne kraje (POL, GER, FRA, ITA, ESP, CZE, etc.)
- Różne kluby
- Różne płcie (M/F)
- Różne kategorie wiekowe
- Różne kategorie wagowe (dla kumite)
- Różne kombinacje dyscyplin (tylko kata, tylko kumite, obie)

### ETAP 4: Generowanie athlete_code
Używamy istniejącego systemu `athlete_code_counter`:
- Format: `{COUNTRY_CODE}{NUMER}` np. `POL001`, `GER001`
- Trzeba zaktualizować counter dla każdego kraju

### ETAP 5: Wstawienie kukiełek
Dla każdej kukiełki:
1. Sprawdź/utwórz athlete_code (użyj funkcji triggera lub ręcznie)
2. Wstaw rekord do `users` z:
   - `is_dummy = true`
   - `auto_category_kata_id` (jeśli kata)
   - `auto_category_kumite_id` (jeśli kumite)
   - `auto_discipline` = 'kata'/'kumite'/'both'
   - Wszystkie wymagane dane (login, password, country_code, etc.)

---

## Przykładowa struktura danych kukiełki

```sql
-- Przykład jednej kukiełki
INSERT INTO karate.users (
    login,
    password,
    country_code,
    nationality,
    club_name,
    first_name,
    last_name,
    sex,
    birth_date,
    weight,
    athlete_code,
    is_dummy,
    auto_category_kata_id,
    auto_category_kumite_id,
    auto_discipline
) VALUES (
    'dummy_pol_001',
    'dummy123',  -- lub NULL jeśli nie potrzebne do logowania
    'POL',
    'Polska',
    'Klub A',
    'Jan',
    'Kowalski',
    'M',
    '2000-01-15',  -- oblicz z kategorii (np. dla kategorii 18-25)
    70.5,  -- pasuje do kategorii wagowej
    'POL001',  -- generowane
    true,  -- is_dummy
    1,  -- auto_category_kata_id (np. Kata M 18-25)
    5,  -- auto_category_kumite_id (np. Kumite M -70kg)
    'both'  -- auto_discipline
);
```

---

## Plan implementacji

### WERSJA 1: Prosty skrypt INSERT z ręcznym przypisaniem
- ~20-30 kukiełek
- Ręcznie przypisane kategorie
- Ręcznie obliczone daty urodzenia i wagi
- Prosty format: `dummy_{country}_{num}`

**Zalety:**
- Proste
- Pełna kontrola
- Łatwe do debugowania

**Wady:**
- Czasochłonne przygotowanie
- Trudne skalowanie

---

### WERSJA 2: Dynamiczny skrypt z pętlami
- Automatyczne generowanie kukiełek dla każdej aktywnej kategorii
- Automatyczne obliczanie wieku/wagi
- Pętle po kategoriach, krajach, klubach

**Zalety:**
- Skalowalne
- Automatyczne
- Zawsze aktualne (nowe kategorie = nowe kukiełki)

**Wady:**
- Bardziej złożone
- Może stworzyć za dużo kukiełek

---

### WERSJA 3: Hybrid - szablon + parametry
- Szablon z przykładami dla każdego typu kategorii
- Funkcja pomocnicza do generowania athlete_code
- Konfigurowalna liczba kukiełek per kategoria

**Zalety:**
- Balans między prostotą a elastycznością
- Łatwe modyfikacje

---

## Rekomendacja: WERSJA 1 (na start)

### Powody:
1. Prostość - łatwo zrozumieć i zmodyfikować
2. Kontrola - wiesz dokładnie co się tworzy
3. Wystarczające dla demonstracji
4. Można później przejść na WERSJĘ 2 jeśli potrzeba

---

## Przykładowa struktura kukiełek (WERSJA 1)

### Podział:
- **10-15 kukiełek MĘSKICH**
  - 5-7 tylko Kata
  - 5-7 tylko Kumite
  - 3-5 obie dyscypliny

- **10-15 kukiełek ŻEŃSKICH**
  - 5-7 tylko Kata
  - 5-7 tylko Kumite
  - 3-5 obie dyscypliny

### Rozkład krajów:
- POL: 5-7
- GER: 3-4
- FRA: 3-4
- ITA: 2-3
- ESP: 2-3
- CZE: 2-3
- Inne: po 1-2

### Rozkład klubów:
- Różne kluby z bazy
- Kilka kukiełek per klub

---

## Następne kroki (do implementacji)

1. **Sprawdzić dostępne kategorie** w bazie
2. **Wybrać reprezentatywny zestaw** kategorii (różne wieki, wagi, płcie)
3. **Przygotować dane** dla ~25 kukiełek
4. **Stworzyć skrypt SQL** z INSERT-ami
5. **Przetestować** tworzenie kukiełek
6. **Przetestować** masową rejestrację
7. **Zweryfikować** że kukiełki zawsze rejestrują się na te same kategorie

---

## UWAGI

- **Login kukiełek**: Może być `dummy_{country}_{num}` - nie będą się logować
- **Password**: Może być `NULL` lub losowe - nie będą się logować
- **athlete_code**: Musi być unikalny, zgodny z formatem `{COUNTRY}{NUMER}`
- **Data urodzenia**: Musi pasować do kategorii wiekowej (np. dla 18-25: urodzony w 2000 = 24 lata w 2024)
- **Waga**: Musi pasować do kategorii wagowej (np. dla -70kg: waga 68-69kg)
- **auto_discipline**: 'kata', 'kumite' lub 'both'
- **auto_category_*_id**: Musi wskazywać na istniejącą aktywną kategorię





