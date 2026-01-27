document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector('.search-form');
    const searchButton = document.querySelector('.search-button');

    if (searchForm && searchButton) {
        // Handle Form Submission
        searchForm.addEventListener('submit', function (e) {
            const input = this.querySelector('input');

            if (input.value.trim() !== "") {
                searchButton.classList.add('loading');
            } else {
                // Stop empty searches
                e.preventDefault();
            }
        });
    }
});

// Reset the button if the user hits the "Back" button
window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        const button = document.querySelector('.search-button');
        if (button) {
            button.classList.remove('loading');
        }
    }
});