// Authentication JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const login = document.getElementById('login').value;
            const password = document.getElementById('password').value;

            try {
                const data = await api.post('/api/login', { login, password });
                utils.showFlash(data.message, 'success');
                setTimeout(() => {
                    window.location.href = '/profile';
                }, 500);
            } catch (error) {
                utils.showFlash(error.message, 'error');
            }
        });
    }

    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        // Load clubs
        loadClubs();

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                login: document.getElementById('login').value,
                password: document.getElementById('password').value,
                country_code: document.getElementById('country_code').value,
                nationality: document.getElementById('nationality').value,
                club_name: document.getElementById('club_name').value,
                first_name: document.getElementById('first_name').value,
                last_name: document.getElementById('last_name').value,
                sex: document.getElementById('sex').value,
                birth_date: document.getElementById('birth_date').value,
                weight: parseFloat(document.getElementById('weight').value)
            };

            try {
                const data = await api.post('/api/register', formData);
                utils.showFlash(data.message, 'success');
                setTimeout(() => {
                    window.location.href = '/profile';
                }, 500);
            } catch (error) {
                utils.showFlash(error.message, 'error');
            }
        });
    }
});

async function loadClubs() {
    try {
        const data = await api.get('/api/clubs');
        const select = document.getElementById('club_name');
        if (select && data.clubs) {
            data.clubs.forEach(club => {
                const option = document.createElement('option');
                option.value = club.name;
                option.textContent = club.name + (club.city ? ` - ${club.city}` : '');
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading clubs:', error);
    }
}

