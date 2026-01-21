/**
 * Pomocnicze funkcje do komunikacji z API
 * Wrapper dla fetch API z obsługą sesji Flask
 */

const api = {
    /**
     * Podstawowa funkcja do wywołań API
     * @param {string} endpoint - endpoint API (np. '/api/profile')
     * @param {object} options - opcje fetch (method, body, etc.)
     * @returns {Promise} - Promise z odpowiedzią JSON
     */
    async request(endpoint, options = {}) {
        const defaultOptions = {
            credentials: 'include', // Ważne dla Flask session (cookies)
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(endpoint, mergedOptions);
            
            // Sprawdź Content-Type przed parsowaniem JSON
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                throw new Error(`Oczekiwano odpowiedzi JSON, otrzymano: ${contentType || 'brak typu'}`);
            }
            
            const data = await response.json();

            if (!response.ok) {
                // Jeśli backend zwróci błąd z komunikatem
                throw new Error(data.error || data.message || `Błąd ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * GET request
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    /**
     * PUT request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    /**
     * DELETE request
     */
    async delete(endpoint, data = null) {
        const options = { method: 'DELETE' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.request(endpoint, options);
    },
};

