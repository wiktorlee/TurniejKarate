// Profile JavaScript

let isEditMode = false;

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    if (path === '/profile') {
        loadProfile();
    } else if (path === '/profile/edit') {
        isEditMode = true;
        loadProfileForEdit();
        setupEditForm();
    }
});

async function loadProfile() {
    const container = document.getElementById('profile-container');
    try {
        const data = await api.get('/api/profile');
        renderProfile(data);
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Błąd podczas ładowania profilu'}
            </div>
        `;
    }
}

function renderProfile(data) {
    const container = document.getElementById('profile-container');
    const user = data.user;
    
    const birthDate = user.birth_date ? new Date(user.birth_date).toISOString().split('T')[0] : 'Brak danych';
    const weight = user.weight ? `${user.weight.toFixed(1)} kg` : 'Brak danych';
    const sex = user.sex === 'M' ? 'Mężczyzna' : user.sex === 'F' ? 'Kobieta' : 'Brak danych';
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Brak danych';

    container.innerHTML = `
        <div class="card" style="padding: 15px; max-width: 500px;">
            <p><b>Login:</b> ${user.login}</p>
            <p><b>Kraj:</b> ${user.country_code}</p>
            <p><b>Narodowość:</b> ${user.nationality || 'Brak danych'}</p>
            <p><b>Klub:</b> ${user.club_name || 'Brak danych'}</p>
            <p><b>Imię i nazwisko:</b> ${fullName}</p>
            <p><b>Płeć:</b> ${sex}</p>
            <p><b>Data urodzenia:</b> ${birthDate}</p>
            <p><b>Waga:</b> ${weight}</p>
            <p><b>Kod zawodnika:</b> ${user.athlete_code || '<i>Nie nadano jeszcze</i>'}</p>
        </div>

        <div style="margin-top: 20px;">
            <a href="/profile/edit" class="btn btn-primary">Edytuj profil</a>
            <a href="/categories" class="btn btn-primary">Zapisz się na zawody</a>
            <a href="/my-registration" class="btn btn-outline-secondary">Moje zgłoszenie</a>
        </div>
    `;
}

async function loadProfileForEdit() {
    try {
        const data = await api.get('/api/profile');
        const user = data.user;
        
        // Fill form fields
        document.getElementById('login').value = user.login;
        document.getElementById('athlete_code').value = user.athlete_code || 'Nie nadano jeszcze';
        document.getElementById('country_code').value = user.country_code || '';
        document.getElementById('nationality').value = user.nationality || '';
        document.getElementById('first_name').value = user.first_name || '';
        document.getElementById('last_name').value = user.last_name || '';
        document.getElementById('sex').value = user.sex || 'M';
        document.getElementById('birth_date').value = user.birth_date || '';
        document.getElementById('weight').value = user.weight || '';
        
        // Load clubs
        const clubSelect = document.getElementById('club_name');
        data.clubs.forEach(club => {
            const option = document.createElement('option');
            option.value = club.name;
            option.textContent = club.name + (club.city ? ` - ${club.city}` : '');
            if (user.club_name === club.name) {
                option.selected = true;
            }
            clubSelect.appendChild(option);
        });
    } catch (error) {
        utils.showFlash(error.message || 'Błąd podczas ładowania profilu', 'error');
    }
}

function setupEditForm() {
    const form = document.getElementById('edit-profile-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            country_code: document.getElementById('country_code').value,
            nationality: document.getElementById('nationality').value,
            club_name: document.getElementById('club_name').value,
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            sex: document.getElementById('sex').value,
            birth_date: document.getElementById('birth_date').value,
            weight: parseFloat(document.getElementById('weight').value),
            password: document.getElementById('password').value
        };
        
        // Remove password if empty
        if (!formData.password) {
            delete formData.password;
        }

        try {
            const data = await api.put('/api/profile', formData);
            utils.showFlash(data.message, 'success');
            setTimeout(() => {
                window.location.href = '/profile';
            }, 500);
        } catch (error) {
            utils.showFlash(error.message, 'error');
        }
    });
}

