// Rankings JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadRankings();
});

async function loadRankings() {
    const container = document.getElementById('rankings-container');
    try {
        const data = await api.get('/api/rankings');
        renderRankings(data);
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ${error.message || 'Błąd podczas ładowania rankingów'}
            </div>
        `;
    }
}

function renderRankings(data) {
    const container = document.getElementById('rankings-container');
    
    let html = `
        <div class="d-flex gap-4 flex-wrap my-4 mb-5">
            ${renderClubRanking(data.club_ranking)}
            ${renderNationRanking(data.nation_ranking)}
        </div>
        <hr>
        <h2 class="mb-4">
          <i class="bi bi-award-fill" style="color: var(--karate-red);"></i>
          Rankingi Indywidualne (Kategorie)
        </h2>
        ${renderIndividualRanking(data.individual_ranking)}
    `;
    
    container.innerHTML = html;
}

function renderClubRanking(clubRanking) {
    if (!clubRanking || clubRanking.length === 0) {
        return `
            <div class="card flex-fill" style="min-width: 300px;">
                <div class="card-header bg-danger text-white">
                    <h3 class="h5 mb-0">
                        <i class="bi bi-building"></i> Ranking Klubowy
                    </h3>
                </div>
                <div class="card-body">
                    <p class="text-muted">Brak danych.</p>
                </div>
            </div>
        `;
    }
    
    let rows = '';
    clubRanking.forEach(item => {
        const medalIcon = item.place === 1 ? '🥇' : item.place === 2 ? '🥈' : item.place === 3 ? '🥉' : '';
        rows += `
            <tr>
                <td><strong>${item.place}${medalIcon ? ' ' + medalIcon : ''}</strong></td>
                <td>${item.name}</td>
                <td><strong class="text-danger">${item.points}</strong></td>
            </tr>
        `;
    });
    
    return `
        <div class="card flex-fill" style="min-width: 300px;">
            <div class="card-header bg-danger text-white">
                <h3 class="h5 mb-0">
                    <i class="bi bi-building"></i> Ranking Klubowy
                </h3>
            </div>
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th><i class="bi bi-trophy-fill"></i> Miejsce</th>
                            <th>Klub</th>
                            <th><i class="bi bi-star-fill"></i> Punkty</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function renderNationRanking(nationRanking) {
    if (!nationRanking || nationRanking.length === 0) {
        return `
            <div class="card flex-fill" style="min-width: 300px;">
                <div class="card-header bg-danger text-white">
                    <h3 class="h5 mb-0">
                        <i class="bi bi-globe"></i> Ranking Narodowościowy
                    </h3>
                </div>
                <div class="card-body">
                    <p class="text-muted">Brak danych.</p>
                </div>
            </div>
        `;
    }
    
    let rows = '';
    nationRanking.forEach(item => {
        const medalIcon = item.place === 1 ? '🥇' : item.place === 2 ? '🥈' : item.place === 3 ? '🥉' : '';
        rows += `
            <tr>
                <td><strong>${item.place}${medalIcon ? ' ' + medalIcon : ''}</strong></td>
                <td><strong>${item.name}</strong></td>
                <td><strong class="text-danger">${item.points}</strong></td>
            </tr>
        `;
    });
    
    return `
        <div class="card flex-fill" style="min-width: 300px;">
            <div class="card-header bg-danger text-white">
                <h3 class="h5 mb-0">
                    <i class="bi bi-globe"></i> Ranking Narodowościowy
                </h3>
            </div>
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th><i class="bi bi-trophy-fill"></i> Miejsce</th>
                            <th><i class="bi bi-flag"></i> Kraj</th>
                            <th><i class="bi bi-star-fill"></i> Punkty</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function renderIndividualRanking(individualRanking) {
    if (!individualRanking || Object.keys(individualRanking).length === 0) {
        return '<p class="text-muted">Brak danych</p>';
    }
    
    let html = '';
    Object.keys(individualRanking).sort().forEach(categoryName => {
        const athletes = individualRanking[categoryName];
        let rows = '';
        
        athletes.forEach(athlete => {
            const medalIcon = athlete.place === 1 ? '🥇' : athlete.place === 2 ? '🥈' : athlete.place === 3 ? '🥉' : '';
            rows += `
                <tr>
                    <td><strong>${athlete.place}${medalIcon ? ' ' + medalIcon : ''}</strong></td>
                    <td>${athlete.first_name} ${athlete.last_name}</td>
                    <td>${athlete.club || '-'}</td>
                    <td>${athlete.country || '-'}</td>
                    <td><strong class="text-danger">${athlete.points}</strong></td>
                </tr>
            `;
        });
        
        html += `
            <div class="card mb-4">
                <div class="card-header bg-light">
                    <h4 class="h5 mb-0">
                        <i class="bi bi-award"></i> ${categoryName}
                    </h4>
                </div>
                <div class="card-body">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th><i class="bi bi-trophy-fill"></i> Miejsce</th>
                                <th>Zawodnik</th>
                                <th>Klub</th>
                                <th><i class="bi bi-flag"></i> Kraj</th>
                                <th><i class="bi bi-star-fill"></i> Punkty</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });
    
    return html;
}

