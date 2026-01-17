// Registration JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    if (path === '/my-registration') {
        loadMyRegistrations();
    }
});

async function loadMyRegistrations() {
    const container = document.getElementById('registrations-container');
    try {
        const data = await api.get('/api/my-registration');
        renderRegistrations(data.registrations);
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Błąd podczas ładowania zgłoszeń'}
            </div>
        `;
    }
}

function renderRegistrations(registrations) {
    const container = document.getElementById('registrations-container');
    
    if (!registrations || registrations.length === 0) {
        container.innerHTML = `
            <p>Nie jesteś jeszcze zapisany do żadnej kategorii.</p>
            <a href="/categories" class="btn btn-primary">Zapisz się teraz</a>
        `;
        return;
    }

    let html = '';
    registrations.forEach(reg => {
        const startDate = reg.start_date ? new Date(reg.start_date).toLocaleDateString('pl-PL') : '';
        const endDate = reg.end_date ? new Date(reg.end_date).toLocaleDateString('pl-PL') : '';
        const dateRange = startDate && endDate ? `${startDate} - ${endDate}` : startDate || endDate || '';
        
        html += `
            <div style="margin-bottom: 24px; padding: 16px; background: #f9f9f9; border-radius: 8px; border: 1px solid #ddd;">
                <h3 style="margin-top: 0; margin-bottom: 12px;">${reg.event_name || 'Brak nazwy eventu'}</h3>
                ${dateRange ? `<p style="margin-bottom: 8px; color: #666;"><b>Termin:</b> ${dateRange}</p>` : ''}
                
                <div style="margin-top: 12px;">
                    ${reg.kata_name ? renderKataSection(reg) : ''}
                    ${reg.kumite_name ? renderKumiteSection(reg) : ''}
                </div>
                
                <form class="withdraw-form" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #ddd;">
                    <input type="hidden" name="registration_id" value="${reg.reg_id}">
                    <button type="submit" class="btn btn-danger btn-sm">
                        Wycofaj całe zgłoszenie na ten event
                    </button>
                </form>
            </div>
        `;
    });

    html += `<p style="margin-top: 16px;"><a href="/categories" class="btn btn-primary">Zapisz się na kolejne zawody</a></p>`;
    container.innerHTML = html;

    // Setup form handlers
    container.querySelectorAll('.withdraw-form').forEach(form => {
        form.addEventListener('submit', handleWithdraw);
    });
    
    container.querySelectorAll('.withdraw-discipline-form').forEach(form => {
        form.addEventListener('submit', handleWithdrawDiscipline);
    });
}

function renderKataSection(reg) {
    const resultHtml = reg.kata_result ? 
        `<p style="margin: 4px 0; color: #28a745; font-weight: bold;">
            Wynik: Miejsce ${reg.kata_result.place}, Punkty: ${reg.kata_result.points}
        </p>` :
        `<p style="margin: 4px 0; color: #666; font-style: italic;">Brak wyniku</p>`;
    
    return `
        <div style="margin-bottom: 8px; padding: 8px; background: white; border-radius: 4px;">
            <p style="margin: 0;"><b>Kata:</b> ${reg.kata_name}</p>
            ${resultHtml}
            <div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="/kata/competitors/${reg.event_id}/${reg.category_kata_id}" class="btn btn-sm btn-primary">
                    Zobacz listę zawodników
                </a>
                <form class="withdraw-discipline-form" style="display: inline;">
                    <input type="hidden" name="registration_id" value="${reg.reg_id}">
                    <input type="hidden" name="discipline_type" value="kata">
                    <button type="submit" class="btn btn-sm btn-danger">Wycofaj z Kata</button>
                </form>
            </div>
        </div>
    `;
}

function renderKumiteSection(reg) {
    const resultHtml = reg.kumite_result ? 
        `<p style="margin: 4px 0; color: #28a745; font-weight: bold;">
            Wynik: Miejsce ${reg.kumite_result.place}
        </p>` :
        `<p style="margin: 4px 0; color: #666; font-style: italic;">Brak wyniku</p>`;
    
    return `
        <div style="margin-bottom: 8px; padding: 8px; background: white; border-radius: 4px;">
            <p style="margin: 0;"><b>Kumite:</b> ${reg.kumite_name}</p>
            ${resultHtml}
            <div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="/kumite/bracket/${reg.event_id}/${reg.category_kumite_id}" class="btn btn-sm btn-primary">
                    Zobacz drzewko walk
                </a>
                <form class="withdraw-discipline-form" style="display: inline;">
                    <input type="hidden" name="registration_id" value="${reg.reg_id}">
                    <input type="hidden" name="discipline_type" value="kumite">
                    <button type="submit" class="btn btn-sm btn-danger">Wycofaj z Kumite</button>
                </form>
            </div>
        </div>
    `;
}

async function handleWithdraw(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const registration_id = formData.get('registration_id');
    
    if (!confirm('Czy na pewno chcesz wycofać to zgłoszenie?')) {
        return;
    }

    try {
        const data = await api.delete('/api/withdraw', { registration_id });
        utils.showFlash(data.message, 'success');
        loadMyRegistrations();
    } catch (error) {
        utils.showFlash(error.message, 'error');
    }
}

async function handleWithdrawDiscipline(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const registration_id = formData.get('registration_id');
    const discipline_type = formData.get('discipline_type');
    
    if (!confirm(`Czy na pewno chcesz wycofać się z ${discipline_type}?`)) {
        return;
    }

    try {
        const data = await api.delete('/api/withdraw-discipline', { registration_id, discipline_type });
        utils.showFlash(data.message, 'success');
        loadMyRegistrations();
    } catch (error) {
        utils.showFlash(error.message, 'error');
    }
}

// Kata competitors
async function loadKataCompetitors(eventId, categoryKataId) {
    const container = document.getElementById('kata-competitors-container');
    try {
        const data = await api.get(`/api/kata/competitors/${eventId}/${categoryKataId}`);
        renderKataCompetitors(data);
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Błąd podczas ładowania listy zawodników'}
            </div>
        `;
    }
}

function renderKataCompetitors(data) {
    const container = document.getElementById('kata-competitors-container');
    const startDate = data.start_date ? new Date(data.start_date).toLocaleDateString('pl-PL') : '';
    const endDate = data.end_date ? new Date(data.end_date).toLocaleDateString('pl-PL') : '';
    const dateRange = startDate && endDate ? `${startDate} - ${endDate}` : startDate || endDate || '';
    
    let html = `
        <h2 style="margin-top: 0;">${data.event_name}</h2>
        <p><b>Kategoria:</b> ${data.category_name}</p>
        ${dateRange ? `<p><b>Termin:</b> ${dateRange}</p>` : ''}
        <p style="margin-top: 16px;"><b>Liczba zawodników:</b> ${data.competitors.length}</p>
    `;
    
    if (data.competitors.length > 0) {
        html += `
            <table class="table table-striped" style="margin-top: 16px;">
                <thead>
                    <tr>
                        <th>Miejsce</th>
                        <th>Kod</th>
                        <th>Imię i nazwisko</th>
                        <th>Kraj</th>
                        <th>Klub</th>
                        <th>Narodowość</th>
                        <th>Punkty</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.competitors.forEach(comp => {
            const rowClass = comp.is_current_user ? 'table-success' : '';
            html += `
                <tr class="${rowClass}">
                    <td>${comp.place ? `<b>${comp.place}</b>` : '<span style="color: #666;">-</span>'}</td>
                    <td><b>${comp.athlete_code}</b>${comp.is_current_user ? ' <small>(Ty)</small>' : ''}</td>
                    <td>${comp.first_name} ${comp.last_name}</td>
                    <td>${comp.country_code}</td>
                    <td>${comp.club_name || '-'}</td>
                    <td>${comp.nationality || '-'}</td>
                    <td>${comp.points !== null ? `<b>${comp.points}</b>` : '<span style="color: #666;">Brak wyniku</span>'}</td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
    } else {
        html += `<p style="margin-top: 16px; color: #666;">Brak zawodników w tej kategorii.</p>`;
    }
    
    html += `<div style="margin-top: 20px;"><a href="/my-registration" class="btn btn-secondary">← Powrót do moich zgłoszeń</a></div>`;
    container.innerHTML = html;
}

// Kumite bracket
async function loadKumiteBracket(eventId, categoryKumiteId) {
    const container = document.getElementById('kumite-bracket-container');
    try {
        const data = await api.get(`/api/kumite/bracket/${eventId}/${categoryKumiteId}`);
        renderKumiteBracket(data);
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Błąd podczas ładowania drzewka walk'}
            </div>
        `;
    }
}

function renderKumiteBracket(data) {
    const container = document.getElementById('kumite-bracket-container');
    const startDate = data.start_date ? new Date(data.start_date).toLocaleDateString('pl-PL') : '';
    const endDate = data.end_date ? new Date(data.end_date).toLocaleDateString('pl-PL') : '';
    const dateRange = startDate && endDate ? `${startDate} - ${endDate}` : startDate || endDate || '';
    
    let html = `
        <h2 style="margin-top: 0;">${data.event_name}</h2>
        <p><b>Kategoria:</b> ${data.category_name}</p>
        ${dateRange ? `<p><b>Termin:</b> ${dateRange}</p>` : ''}
        <p style="margin-top: 16px; margin-bottom: 12px; color: #666;"><b>Liczba pojedynków:</b> ${data.fights_list.length}</p>
    `;
    
    if (data.fights_list.length > 0) {
        data.fights_list.forEach(fight => {
            const fightClass = fight.is_current_user ? 'border border-primary bg-light' : '';
            html += `
                <div class="card mb-3 ${fightClass}">
                    <div class="card-body">
                        <div class="fw-bold mb-2 text-muted">
                            Pojedynek ${fight.fight_no}
                            ${fight.is_finished ? 
                                '<span class="text-success ms-2">Zakończona</span>' : 
                                '<span class="text-warning ms-2">W toku</span>'
                            }
                        </div>
                        <div class="d-flex align-items-center gap-3 flex-wrap">
                            <div class="flex-fill">
                                <div class="text-danger fw-bold">${fight.red_code}</div>
                                <div>${fight.red_name}</div>
                                ${fight.red_country ? `<div class="small text-muted">${fight.red_country}${fight.red_club ? ` - ${fight.red_club}` : ''}</div>` : ''}
                                ${fight.red_score !== null ? `<div class="fw-bold text-danger mt-1" style="font-size: 1.2em;">${fight.red_score}</div>` : ''}
                                ${fight.winner_code === fight.red_code ? '<div class="text-success fw-bold mt-1">Zwycięzca</div>' : ''}
                            </div>
                            <div class="fw-bold text-muted">vs</div>
                            <div class="flex-fill">
                                ${fight.is_bye ? 
                                    `<div class="text-muted fw-bold">[BYE]</div>
                                     <div class="text-muted fst-italic">Wolny los</div>` :
                                    `<div class="text-primary fw-bold">${fight.blue_code}</div>
                                     <div>${fight.blue_name}</div>
                                     ${fight.blue_country ? `<div class="small text-muted">${fight.blue_country}${fight.blue_club ? ` - ${fight.blue_club}` : ''}</div>` : ''}
                                     ${fight.blue_score !== null ? `<div class="fw-bold text-primary mt-1" style="font-size: 1.2em;">${fight.blue_score}</div>` : ''}
                                     ${fight.winner_code === fight.blue_code ? '<div class="text-success fw-bold mt-1">Zwycięzca</div>' : ''}`
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
    } else {
        html += `<p style="margin-top: 16px; color: #666;">Brak pojedynków w tej kategorii. Uruchom symulację zawodów.</p>`;
    }
    
    html += `<div style="margin-top: 20px;"><a href="/my-registration" class="btn btn-secondary">← Powrót do moich zgłoszeń</a></div>`;
    container.innerHTML = html;
}

