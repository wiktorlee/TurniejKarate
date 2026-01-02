/**
 * Pomocnicze funkcje do formatowania i manipulacji danymi
 */

const utils = {
    /**
     * Formatuje datę do wyświetlenia (YYYY-MM-DD)
     */
    formatDate(dateString) {
        if (!dateString) return 'Brak danych';
        const date = new Date(dateString);
        return date.toISOString().split('T')[0];
    },

    /**
     * Formatuje wagę z 2 miejscami po przecinku
     */
    formatWeight(weight) {
        if (!weight) return 'Brak danych';
        return `${parseFloat(weight).toFixed(1)} kg`;
    },

    /**
     * Formatuje płeć do wyświetlenia
     */
    formatSex(sex) {
        if (sex === 'M') return 'Mężczyzna';
        if (sex === 'F') return 'Kobieta';
        return 'Brak danych';
    },

    /**
     * Wyświetla komunikat flash (błąd/sukces)
     */
    showFlash(message, type = 'info') {
        // Znajdź lub utwórz kontener na komunikaty
        let flashContainer = document.getElementById('flash-messages');
        if (!flashContainer) {
            flashContainer = document.createElement('div');
            flashContainer.id = 'flash-messages';
            const main = document.querySelector('main') || document.body;
            main.insertBefore(flashContainer, main.firstChild);
        }

        const flashDiv = document.createElement('div');
        flashDiv.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}`;
        flashDiv.textContent = message;
        flashDiv.setAttribute('role', 'alert');
        
        flashContainer.appendChild(flashDiv);

        // Usuń po 5 sekundach
        setTimeout(() => {
            flashDiv.remove();
        }, 5000);
    },

    /**
     * Przekierowanie na inną stronę
     */
    redirect(url) {
        window.location.href = url;
    },
};

