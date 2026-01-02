// Admin JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

async function loadDashboard() {
    const container = document.getElementById('admin-dashboard-container');
    try {
        const data = await api.get('/api/admin/dashboard');
        renderDashboard(data);
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Błąd podczas ładowania panelu'}
            </div>
        `;
    }
}

function renderDashboard(data) {
    const container = document.getElementById('admin-dashboard-container');
    const status = data.system_status;
    
    let statusColor = 'green';
    let statusText = status.status;
    if (status.status === 'SIMULATED') {
        statusColor = 'orange';
        statusText = 'SYMULOWANY';
    } else if (status.status !== 'ACTIVE') {
        statusColor = 'red';
        statusText = 'ZAMKNIĘTY';
    }
    
    const simulationDate = status.simulation_date ? new Date(status.simulation_date).toLocaleString('pl-PL') : '';
    const resetDate = status.reset_date ? new Date(status.reset_date).toLocaleString('pl-PL') : '';
    const updatedAt = status.updated_at ? new Date(status.updated_at).toLocaleString('pl-PL') : '';
    
    container.innerHTML = `
        <div class="card mb-3">
            <h2>Status Systemu</h2>
            <p><strong>Status:</strong> <span style="color: ${statusColor};">${statusText}</span></p>
            ${simulationDate ? `<p><strong>Data symulacji:</strong> ${simulationDate}</p>` : ''}
            ${resetDate ? `<p><strong>Data ostatniego resetu:</strong> ${resetDate}</p>` : ''}
            ${updatedAt ? `<p><strong>Ostatnia aktualizacja:</strong> ${updatedAt}</p>` : ''}
        </div>

        <div class="card mb-3">
            <h2>Statystyki</h2>
            <p>Kukiełki w systemie: <strong>${data.dummy_count}</strong></p>
            <p>Aktywne eventy: <strong>${data.active_events}</strong></p>
            <p>Wyniki w bazie: <strong>${data.results_count}</strong></p>
            <p>Rejestracje w bazie: <strong>${data.registrations_count}</strong></p>
        </div>

        <div class="card">
            <h2>Akcje Administracyjne</h2>
            
            <div class="p-4 bg-light rounded mb-3">
                <h3>Masowa rejestracja kukiełek</h3>
                <p class="mb-2">Rejestruje wszystkie kukiełki do aktywnych eventów zgodnie z ich przypisanymi kategoriami.</p>
                <p class="small text-muted mb-2">Procedura SQL sprawdza czy rejestracje już istnieją, więc można wywołać bezpiecznie wielokrotnie.</p>
                <button class="btn btn-primary" onclick="restoreDummyAthletes()">
                    Zarejestruj kukiełki
                </button>
            </div>
            
            <div class="p-4 bg-warning bg-opacity-10 border border-warning rounded mb-3">
                <h3>Reset systemu</h3>
                <p class="mb-2"><strong>UWAGA:</strong> To usunie wszystkie wyniki i drzewka walk. System wróci do stanu początkowego.</p>
                <div class="mb-2">
                    <label class="d-flex align-items-center gap-2">
                        <input type="checkbox" id="restore-dummies-checkbox">
                        <span>Przywróć rejestracje kukiełek po resecie</span>
                    </label>
                </div>
                <button class="btn btn-danger" onclick="resetSystem()">
                    Zresetuj system
                </button>
            </div>
            
            <div class="p-4 bg-info bg-opacity-10 border border-info rounded">
                <h3>Symulacja sezonu</h3>
                <p class="mb-2">Losuje wyniki dla wszystkich aktywnych eventów i aktualizuje rankingi.</p>
                <p class="small text-muted mb-2">Status systemu zmieni się na SIMULATED po zakończeniu symulacji.</p>
                <button class="btn btn-success" onclick="simulateSeason()" ${status.status === 'SIMULATED' ? 'disabled' : ''}>
                    ${status.status === 'SIMULATED' ? 'Symulacja już przeprowadzona' : 'Uruchom symulację'}
                </button>
            </div>
        </div>

        <div class="mt-4">
            <a href="/" class="btn btn-secondary">← Powrót do strony głównej</a>
        </div>
    `;
}

async function restoreDummyAthletes() {
    if (!confirm('Czy na pewno chcesz zarejestrować wszystkie kukiełki do aktywnych eventów?')) {
        return;
    }

    try {
        const data = await api.post('/api/admin/restore-dummy-athletes', {});
        utils.showFlash(data.message, data.info ? 'info' : 'success');
        loadDashboard();
    } catch (error) {
        utils.showFlash(error.message, 'error');
    }
}

async function resetSystem() {
    if (!confirm('UWAGA: To usunie wszystkie wyniki i drzewka walk. Czy na pewno chcesz kontynuować?')) {
        return;
    }

    const restoreDummies = document.getElementById('restore-dummies-checkbox').checked;

    try {
        const data = await api.post('/api/admin/reset', { restore_dummies: restoreDummies });
        utils.showFlash(data.message, 'success');
        loadDashboard();
    } catch (error) {
        utils.showFlash(error.message, 'error');
    }
}

async function simulateSeason() {
    if (!confirm('Czy na pewno chcesz przeprowadzić symulację sezonu?')) {
        return;
    }

    try {
        const data = await api.post('/api/admin/simulate', {});
        utils.showFlash(data.message, 'success');
        loadDashboard();
    } catch (error) {
        utils.showFlash(error.message, error.warning ? 'warning' : 'error');
        if (!error.warning) {
            loadDashboard();
        }
    }
}

