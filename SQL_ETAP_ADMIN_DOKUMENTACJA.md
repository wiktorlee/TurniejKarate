# Dokumentacja SQL - Etap Administracja i Kukiełki

## Przegląd
Dokumentacja zawiera wszystkie skrypty SQL użyte do implementacji panelu administratorskiego, systemu statusu oraz funkcjonalności kukiełek (sztucznych zawodników).

---

## 1. MODYFIKACJA TABELI `users`

### 1.1. Dodanie kolumny `is_admin`
Flaga administratora w tabeli użytkowników.

```sql
ALTER TABLE karate.users 
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL;
```

**Weryfikacja:**
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_schema = 'karate' 
  AND table_name = 'users' 
  AND column_name = 'is_admin';
```

---

### 1.2. Dodanie kolumny `is_dummy`
Flaga oznaczająca kukiełkę (sztucznego zawodnika).

```sql
ALTER TABLE karate.users 
ADD COLUMN IF NOT EXISTS is_dummy BOOLEAN DEFAULT FALSE NOT NULL;
```

---

### 1.3. Dodanie kolumny `auto_category_kata_id`
ID kategorii kata, do której kukiełka będzie się automatycznie rejestrowała.

```sql
ALTER TABLE karate.users 
ADD COLUMN IF NOT EXISTS auto_category_kata_id INTEGER;
```

**Dodanie foreign key:**
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_schema = 'karate' 
        AND table_name = 'users' 
        AND constraint_name = 'users_auto_category_kata_id_fkey'
    ) THEN
        ALTER TABLE karate.users 
        ADD CONSTRAINT users_auto_category_kata_id_fkey 
        FOREIGN KEY (auto_category_kata_id) 
        REFERENCES karate.categories_kata(id);
    END IF;
END $$;
```

---

### 1.4. Dodanie kolumny `auto_category_kumite_id`
ID kategorii kumite, do której kukiełka będzie się automatycznie rejestrowała.

```sql
ALTER TABLE karate.users 
ADD COLUMN IF NOT EXISTS auto_category_kumite_id INTEGER;
```

**Dodanie foreign key:**
```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_schema = 'karate' 
        AND table_name = 'users' 
        AND constraint_name = 'users_auto_category_kumite_id_fkey'
    ) THEN
        ALTER TABLE karate.users 
        ADD CONSTRAINT users_auto_category_kumite_id_fkey 
        FOREIGN KEY (auto_category_kumite_id) 
        REFERENCES karate.categories_kumite(id);
    END IF;
END $$;
```

---

### 1.5. Dodanie kolumny `auto_discipline`
Określa, do której dyscypliny kukiełka będzie się rejestrowała: 'kata', 'kumite' lub 'both'.

```sql
ALTER TABLE karate.users 
ADD COLUMN IF NOT EXISTS auto_discipline TEXT CHECK (auto_discipline IS NULL OR auto_discipline IN ('kata', 'kumite', 'both'));
```

**Weryfikacja wszystkich kolumn kukiełek:**
```sql
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_schema = 'karate' 
  AND table_name = 'users' 
  AND column_name IN ('is_dummy', 'auto_category_kata_id', 'auto_category_kumite_id', 'auto_discipline')
ORDER BY column_name;
```

---

## 2. UTWORZENIE TABELI `system_status`

### 2.1. Definicja tabeli
Tabela zarządzająca statusem systemu (ACTIVE/SIMULATED).

```sql
CREATE TABLE IF NOT EXISTS karate.system_status (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SIMULATED')),
    season_name TEXT,
    simulation_date TIMESTAMP WITH TIME ZONE,
    reset_date TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Wstawienie początkowego statusu:**
```sql
INSERT INTO karate.system_status (status)
SELECT 'ACTIVE'
WHERE NOT EXISTS (SELECT 1 FROM karate.system_status);
```

**Weryfikacja:**
```sql
SELECT * FROM karate.system_status;
```

---

## 3. PROCEDURA SQL: `restore_dummy_athletes_registrations()`

### 3.1. Usunięcie starej wersji (jeśli istnieje)
```sql
DROP FUNCTION IF EXISTS karate.restore_dummy_athletes_registrations();
```

### 3.2. Definicja procedury
Procedura masowo rejestruje wszystkie kukiełki (`is_dummy = true`) do aktywnych eventów zgodnie z ich przypisanymi kategoriami (`auto_category_kata_id`, `auto_category_kumite_id`) i dyscypliną (`auto_discipline`).

```sql
CREATE OR REPLACE FUNCTION karate.restore_dummy_athletes_registrations()
RETURNS TABLE (
    message TEXT,
    athlete_code TEXT,
    registrations_created INTEGER
) 
LANGUAGE plpgsql
AS $$
DECLARE
    dummy_user RECORD;
    active_event RECORD;
    reg_count INTEGER := 0;
    total_registrations INTEGER := 0;
BEGIN
    -- Sprawdź czy są kukiełki
    IF NOT EXISTS (SELECT 1 FROM karate.users WHERE is_dummy = true) THEN
        RETURN QUERY SELECT 'Brak kukiełek do zarejestrowania'::TEXT, NULL::TEXT, 0::INTEGER;
        RETURN;
    END IF;

    -- Dla każdej kukiełki
    FOR dummy_user IN 
        SELECT athlete_code, auto_category_kata_id, auto_category_kumite_id, auto_discipline
        FROM karate.users 
        WHERE is_dummy = true
    LOOP
        reg_count := 0;
        
        -- Dla każdego aktywnego eventu
        FOR active_event IN 
            SELECT id FROM karate.events WHERE is_active = true
        LOOP
            -- Sprawdź czy kukiełka powinna być zapisana do kata
            IF (dummy_user.auto_discipline IN ('kata', 'both') AND dummy_user.auto_category_kata_id IS NOT NULL) THEN
                -- Sprawdź czy rejestracja już istnieje
                IF NOT EXISTS (
                    SELECT 1 FROM karate.registrations 
                    WHERE athlete_code = dummy_user.athlete_code 
                    AND event_id = active_event.id 
                    AND category_kata_id = dummy_user.auto_category_kata_id
                ) THEN
                    -- Utwórz rejestrację dla kata
                    INSERT INTO karate.registrations 
                    (athlete_code, event_id, category_kata_id)
                    VALUES (dummy_user.athlete_code, active_event.id, dummy_user.auto_category_kata_id);
                    reg_count := reg_count + 1;
                END IF;
            END IF;
            
            -- Sprawdź czy kukiełka powinna być zapisana do kumite
            IF (dummy_user.auto_discipline IN ('kumite', 'both') AND dummy_user.auto_category_kumite_id IS NOT NULL) THEN
                -- Sprawdź czy rejestracja już istnieje
                IF NOT EXISTS (
                    SELECT 1 FROM karate.registrations 
                    WHERE athlete_code = dummy_user.athlete_code 
                    AND event_id = active_event.id 
                    AND category_kumite_id = dummy_user.auto_category_kumite_id
                ) THEN
                    -- Utwórz rejestrację dla kumite
                    INSERT INTO karate.registrations 
                    (athlete_code, event_id, category_kumite_id)
                    VALUES (dummy_user.athlete_code, active_event.id, dummy_user.auto_category_kumite_id);
                    reg_count := reg_count + 1;
                END IF;
            END IF;
        END LOOP;
        
        -- Zwróć wynik dla tej kukiełki
        IF reg_count > 0 THEN
            RETURN QUERY SELECT 'Zarejestrowano'::TEXT, dummy_user.athlete_code, reg_count;
            total_registrations := total_registrations + reg_count;
        END IF;
    END LOOP;
    
    -- Jeśli nie utworzono żadnych rejestracji
    IF total_registrations = 0 THEN
        RETURN QUERY SELECT 'Wszystkie kukiełki już zarejestrowane lub brak aktywnych eventów'::TEXT, NULL::TEXT, 0::INTEGER;
    END IF;
END;
$$;
```

**Weryfikacja:**
```sql
SELECT routine_name, routine_type
FROM information_schema.routines 
WHERE routine_schema = 'karate' 
  AND routine_name = 'restore_dummy_athletes_registrations';
```

**Opis działania:**
- Procedura przegląda wszystkich użytkowników z `is_dummy = true`
- Dla każdej kukiełki i każdego aktywnego eventu:
  - Sprawdza `auto_discipline` (kata/kumite/both)
  - Jeśli pasuje, sprawdza czy rejestracja już istnieje (zapobieganie duplikatom)
  - Jeśli nie istnieje, tworzy nową rejestrację z odpowiednią kategorią
- Zwraca tabelę z informacjami o zarejestrowanych kukiełkach

---

## 4. KONFIGURACJA KONTA ADMINISTRATORA

### 4.1. Sprawdzenie istniejących kont
```sql
SELECT id, login, is_admin FROM karate.users ORDER BY id;
```

### 4.2. Ustawienie konta jako administrator
```sql
UPDATE karate.users SET is_admin = true WHERE login = 'twoj_login';
```

**Weryfikacja:**
```sql
SELECT id, login, is_admin FROM karate.users WHERE is_admin = true;
```

---

## 5. ZAPYTANIA WERYFIKUJĄCE (PODSUMOWANIE)

### 5.1. Weryfikacja wszystkich elementów
```sql
-- Sprawdź kolumnę is_admin
SELECT 'Kolumna is_admin:' as info, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'karate' AND table_name = 'users' AND column_name = 'is_admin';

-- Sprawdź tabelę system_status
SELECT 'Tabela system_status:' as info, COUNT(*) as rows_count 
FROM karate.system_status;

-- Sprawdź kolumny kukiełek
SELECT 'Kolumny kukiełek:' as info, column_name 
FROM information_schema.columns 
WHERE table_schema = 'karate' 
  AND table_name = 'users' 
  AND column_name IN ('is_dummy', 'auto_category_kata_id', 'auto_category_kumite_id', 'auto_discipline')
ORDER BY column_name;

-- Sprawdź procedurę
SELECT 'Procedura:' as info, routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'karate' 
  AND routine_name = 'restore_dummy_athletes_registrations';
```

---

## PODSUMOWANIE DODANYCH ELEMENTÓW

| Element | Typ | Opis |
|---------|-----|------|
| `users.is_admin` | Kolumna BOOLEAN | Flaga administratora |
| `users.is_dummy` | Kolumna BOOLEAN | Flaga kukiełki |
| `users.auto_category_kata_id` | Kolumna INTEGER (FK) | Auto-kategoria kata |
| `users.auto_category_kumite_id` | Kolumna INTEGER (FK) | Auto-kategoria kumite |
| `users.auto_discipline` | Kolumna TEXT (CHECK) | Dyscyplina auto-rejestracji |
| `system_status` | Tabela | Zarządzanie statusem systemu |
| `restore_dummy_athletes_registrations()` | Procedura SQL | Masowa rejestracja kukiełek |

---

## UŻYCIE W KODZIE PYTHON

### Weryfikacja uprawnień admina:
```python
# routes/admin.py - dekorator @require_admin
cur.execute(f"SELECT is_admin FROM {SCHEMA}.users WHERE id = %s", (uid,))
```

### Sprawdzenie statusu systemu:
```python
# routes/categories.py
cur.execute(f"SELECT status FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1")
```

### Wywołanie procedury rejestracji kukiełek:
```python
# routes/admin.py
cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
```

---

## UWAGI

1. Wszystkie `ALTER TABLE` używa `IF NOT EXISTS` dla bezpieczeństwa
2. Procedura sprawdza duplikaty przed wstawieniem rejestracji
3. Procedura jest idempotentna - można ją wywołać wielokrotnie bezpiecznie
4. Foreign keys zapewniają integralność danych (kategorie muszą istnieć)
5. CHECK constraint na `auto_discipline` ogranicza dozwolone wartości














