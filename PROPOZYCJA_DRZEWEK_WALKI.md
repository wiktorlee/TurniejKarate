# Propozycja rozwiązania: System drzewek walki

## 1. Analiza obecnej sytuacji

### Obecna struktura bazy danych:
- **`registrations`** - przechowuje zapisy zawodników na zawody z kategoriami kata/kumite
- **`draw_fight`** - już istnieje tabela do przechowywania pojedynków (round_no=1, red_code, blue_code, category_id)
- **`categories_kumite`** i **`categories_kata`** - kategorie
- **`users`** - zawodnicy z `athlete_code`

### Obecna funkcjonalność:
- System rejestracji zawodników
- System zapisów na zawody (kata i kumite)
- Wyświetlanie własnego zgłoszenia

---

## 2. Wymagania funkcjonalne

### 2.1. Kumite - Drzewko walk (Brackets)
- Po zapisie na kumite: wyświetlenie drzewka walk
- Losowe lub alfabetyczne przydzielanie zawodników do pojedynków
- Na razie tylko pierwsze pojedynki widoczne (round_no = 1)
- Docelowo: symulacja wyników i rankingi (faza przyszła)

### 2.2. Kata - Lista zawodników
- Po zapisie na kata: wyświetlenie listy zapisanych zawodników do kategorii
- Prosta lista z danymi zawodników

---

## 3. Proponowane rozwiązanie

### 3.1. Architektura rozwiązania

#### A. Endpointy (nowe route: `routes/brackets.py`)

1. **`GET /brackets/kumite/<category_id>`**
   - Wyświetla drzewko walk dla kategorii kumite
   - Generuje pojedynki jeśli nie istnieją
   - Opcje: losowe/alfabetyczne przydzielanie

2. **`GET /brackets/kata/<category_id>`**
   - Wyświetla listę zawodników zapisanych do kategorii kata

3. **`POST /brackets/generate/<category_id>`**
   - Generuje/regeneruje drzewko dla kategorii kumite
   - Parametr: `method` (random/alphabetical)

#### B. Logika generowania drzewka (Kumite)

**Algorytm:**
1. Pobierz wszystkich zapisanych zawodników do kategorii
2. Jeśli liczba zawodników nieparzysta → dodaj "BYE" (wolny los)
3. Oblicz liczbę pojedynków w pierwszej rundzie: `ceil(n/2)`
4. Przydziel zawodników:
   - **Alfabetycznie**: sortuj po `athlete_code` lub `last_name, first_name`
   - **Losowo**: użyj `random.shuffle()`
5. Utwórz wpisy w `draw_fight` dla pierwszej rundy (round_no=1)

**Przykład dla 8 zawodników:**
```
Runda 1:
  Fight 1: Zawodnik A vs Zawodnik B
  Fight 2: Zawodnik C vs Zawodnik D
  Fight 3: Zawodnik E vs Zawodnik F
  Fight 4: Zawodnik G vs Zawodnik H
```

**Przykład dla 7 zawodników (z BYE):**
```
Runda 1:
  Fight 1: Zawodnik A vs Zawodnik B
  Fight 2: Zawodnik C vs Zawodnik D
  Fight 3: Zawodnik E vs Zawodnik F
  Fight 4: Zawodnik G vs BYE
```

#### C. Wyświetlanie drzewka

**Opcje wizualizacji:**
1. **Prosta lista pojedynków** (na start - łatwiejsze)
   - Lista pojedynków z numerami
   - Zawodnik czerwony vs zawodnik niebieski

2. **Wizualne drzewko (brackets)** (docelowo)
   - Użycie biblioteki JS: `bracket-generator` lub własna implementacja CSS
   - Wizualne przedstawienie struktury turnieju

**Na razie proponuję: prostą listę pojedynków** - łatwiejsze w implementacji, wystarczające na start.

---

### 3.2. Struktura danych

#### Tabela `draw_fight` (już istnieje):
```sql
- id
- category_id (FK → categories_kumite.id)
- round_no (CHECK = 1) - na razie tylko runda 1
- fight_no (numer pojedynku w rundzie)
- red_code (FK → users.athlete_code)
- blue_code (FK → users.athlete_code)
- created_at
```

**Uwaga:** Tabela `draw_fight` ma `category_id` → `categories(id)`, ale powinniśmy używać `categories_kumite(id)`. 
**Propozycja:** Dodać kolumnę `category_kumite_id` lub zmienić referencję.

**Lepsze rozwiązanie:** Dodać kolumnę `category_kumite_id` do `draw_fight`:
```sql
ALTER TABLE karate.draw_fight 
ADD COLUMN category_kumite_id integer REFERENCES karate.categories_kumite(id);
```

Lub użyć istniejącej `category_id` jeśli wskazuje na odpowiednią kategorię.

#### Dane do wyświetlenia:
- Dla Kumite: lista pojedynków z danymi zawodników (imię, nazwisko, kod)
- Dla Kata: lista zawodników (imię, nazwisko, kod, klub)

---

### 3.3. Integracja z obecnym systemem

#### Modyfikacja `my_registration.html`:
- Dodać linki do drzewek/list:
  - "Zobacz drzewko walk" (jeśli kumite)
  - "Zobacz listę zawodników" (jeśli kata)

#### Nowy widok:
- `templates/brackets_kumite.html` - drzewko walk
- `templates/brackets_kata.html` - lista zawodników

---

## 4. Szczegóły implementacji

### 4.1. Funkcje pomocnicze

```python
# routes/brackets.py

def get_registered_athletes(category_kumite_id):
    """Pobiera listę zapisanych zawodników do kategorii kumite"""
    # SELECT athlete_code, first_name, last_name FROM registrations 
    # WHERE category_kumite_id = ? AND status = 'pending' (lub aktywne)
    
def generate_bracket(category_kumite_id, method='random'):
    """Generuje drzewko walk dla kategorii"""
    # 1. Pobierz zawodników
    # 2. Sortuj lub losuj
    # 3. Utwórz pary
    # 4. Wstaw do draw_fight
    
def get_bracket(category_kumite_id):
    """Pobiera istniejące drzewko walk"""
    # SELECT * FROM draw_fight WHERE category_kumite_id = ? ORDER BY fight_no
```

### 4.2. Endpointy

```python
@brackets_bp.route("/brackets/kumite/<int:category_id>")
def view_kumite_bracket(category_id):
    # Sprawdź czy drzewko istnieje
    # Jeśli nie → wygeneruj (domyślnie losowo)
    # Wyświetl drzewko
    
@brackets_bp.route("/brackets/kata/<int:category_id>")
def view_kata_list(category_id):
    # Pobierz listę zawodników zapisanych do kategorii kata
    # Wyświetl listę
    
@brackets_bp.route("/brackets/generate/<int:category_id>", methods=["POST"])
def generate_bracket_endpoint(category_id):
    # method = request.form.get("method", "random")
    # Wygeneruj/regeneruj drzewko
    # Redirect do widoku drzewka
```

### 4.3. Obsługa nieparzystej liczby zawodników

**Opcje:**
1. **BYE (wolny los)** - jeden zawodnik przechodzi bez walki
2. **Automatyczny awans** - najwyżej rozstawiony zawodnik przechodzi

**Propozycja:** BYE - prostsze i standardowe w turniejach.

---

## 5. Plan implementacji (kroki)

### Krok 1: Przygotowanie bazy danych
- Sprawdzenie/aktualizacja tabeli `draw_fight`
- Ewentualna migracja jeśli potrzeba

### Krok 2: Utworzenie blueprintu `brackets.py`
- Funkcje pomocnicze
- Endpointy

### Krok 3: Szablony HTML
- `brackets_kumite.html` - lista pojedynków
- `brackets_kata.html` - lista zawodników

### Krok 4: Integracja z `my_registration.html`
- Dodanie linków do drzewek/list

### Krok 5: Testy
- Testowanie z różną liczbą zawodników
- Testowanie losowego i alfabetycznego przydzielania

---

## 6. Uwagi techniczne

### 6.1. Status rejestracji
- Sprawdzić czy `registrations.status` jest używany
- Jeśli tak, filtrować tylko aktywne zgłoszenia

### 6.2. Bezpieczeństwo
- Sprawdzenie czy użytkownik ma dostęp do kategorii
- Walidacja `category_id`

### 6.3. Wydajność
- Indeksy na `draw_fight.category_kumite_id` (lub `category_id`)
- Indeksy na `registrations.category_kumite_id`

### 6.4. Przyszłe rozszerzenia
- Rundy 2, 3, ... (finał)
- Symulacja wyników
- System rankingowy
- Eksport do PDF

---

## 7. Przykładowy widok drzewka (prosta lista)

```
Drzewko walk - Kategoria: Kumite Mężczyźni -60kg

Runda 1:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pojedynek 1:
  🔴 Czerwony: POL001 - Jan Kowalski
  🔵 Niebieski: POL002 - Piotr Nowak
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pojedynek 2:
  🔴 Czerwony: POL003 - Adam Wiśniewski
  🔵 Niebieski: POL004 - Tomasz Zieliński
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

---

## 8. Przykładowy widok listy Kata

```
Lista zawodników - Kategoria: Kata Kobiety

1. POL001 - Anna Kowalska (Klub: Warszawa)
2. POL002 - Maria Nowak (Klub: Kraków)
3. POL003 - Katarzyna Wiśniewska (Klub: Gdańsk)
...
```

---

## 9. Pytania do rozstrzygnięcia

1. **Tabela `draw_fight`**: Czy `category_id` wskazuje na `categories_kumite` czy `categories`? 
   - **Propozycja:** Dodać `category_kumite_id` dla jasności

2. **Status rejestracji**: Czy filtrować po `status = 'pending'` czy wszystkie?
   - **Propozycja:** Wszystkie aktywne (bez wycofanych)

3. **Regeneracja drzewka**: Czy pozwolić na regenerację (np. przez admina)?
   - **Propozycja:** Tak, ale z ostrzeżeniem

4. **Dostęp do drzewek**: Czy tylko dla zapisanych zawodników czy publiczny?
   - **Propozycja:** Publiczny dla kategorii (każdy może zobaczyć)

---

## 10. Rekomendacja

**Proponuję rozpocząć od:**
1. Prostej listy pojedynków (nie pełne drzewko wizualne)
2. Losowego przydzielania jako domyślnego
3. Publicznego dostępu do drzewek/list
4. Automatycznego generowania przy pierwszym wyświetleniu

**To da nam:**
- Szybką implementację
- Działającą funkcjonalność
- Możliwość rozbudowy w przyszłości

---

## Podsumowanie

Rozwiązanie jest proste, skalowalne i łatwe do rozbudowy. Wykorzystuje istniejącą strukturę bazy danych i integruje się z obecnym systemem rejestracji. Można je wdrożyć etapami, zaczynając od podstawowej funkcjonalności.




