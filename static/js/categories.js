// Categories JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    setupForm();
});

async function loadCategories() {
    try {
        const data = await api.get('/api/categories');
        renderCategories(data);
        
        if (data.has_registration) {
            document.getElementById('has-registration-info').style.display = 'block';
        }
    } catch (error) {
        if (error.message.includes('zakończonym')) {
            utils.showFlash(error.message, 'error');
            setTimeout(() => {
                window.location.href = '/rankings';
            }, 2000);
        } else {
            utils.showFlash(error.message || 'Błąd podczas ładowania kategorii', 'error');
        }
    }
}

function renderCategories(data) {
    // Populate events
    const eventSelect = document.getElementById('event_select');
    data.events.forEach(event => {
        const option = document.createElement('option');
        option.value = event.id;
        option.textContent = event.name;
        eventSelect.appendChild(option);
    });

    // Populate Kata categories
    const kataSelect = document.getElementById('category_kata_select');
    data.categories_kata.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        kataSelect.appendChild(option);
    });

    // Populate Kumite categories
    const kumiteSelect = document.getElementById('category_kumite_select');
    data.categories_kumite.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        kumiteSelect.appendChild(option);
    });

    // Setup checkbox handlers
    document.getElementById('discipline_kata').addEventListener('change', toggleKataCategories);
    document.getElementById('discipline_kumite').addEventListener('change', toggleKumiteCategories);
}

function toggleKataCategories() {
    const checkbox = document.getElementById('discipline_kata');
    const section = document.getElementById('kata_section');
    const select = document.getElementById('category_kata_select');
    if (checkbox.checked) {
        section.style.display = 'block';
        select.required = true;
    } else {
        section.style.display = 'none';
        select.required = false;
        select.value = '';
    }
}

function toggleKumiteCategories() {
    const checkbox = document.getElementById('discipline_kumite');
    const section = document.getElementById('kumite_section');
    const select = document.getElementById('category_kumite_select');
    if (checkbox.checked) {
        section.style.display = 'block';
        select.required = true;
    } else {
        section.style.display = 'none';
        select.required = false;
        select.value = '';
    }
}

function setupForm() {
    const form = document.getElementById('registration-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            event_id: parseInt(document.getElementById('event_select').value),
            discipline_kata: document.getElementById('discipline_kata').checked,
            discipline_kumite: document.getElementById('discipline_kumite').checked,
            category_kata_id: document.getElementById('category_kata_select').value ? 
                parseInt(document.getElementById('category_kata_select').value) : null,
            category_kumite_id: document.getElementById('category_kumite_select').value ? 
                parseInt(document.getElementById('category_kumite_select').value) : null
        };

        try {
            const data = await api.post('/api/categories/register', formData);
            utils.showFlash(data.message, 'success');
            setTimeout(() => {
                window.location.href = '/my-registration';
            }, 1000);
        } catch (error) {
            utils.showFlash(error.message, 'error');
        }
    });
}

