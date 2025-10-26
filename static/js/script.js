console.log("Skyvela frontend connected successfully!");

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('flightForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const origin = document.getElementById('origin').value;
            const destination = document.getElementById('destination').value;
            const date = document.getElementById('date').value;

            document.getElementById('results').innerHTML =
                `<p>Searching flights from <strong>${origin}</strong> to <strong>${destination}</strong> on <strong>${date}</strong>...</p>`;
        });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const sortSelect = document.getElementById('sort-options');
    const flightsContainer = document.getElementById('flights-container');

    if (sortSelect && flightsContainer) {
        sortSelect.addEventListener('change', () => {
            alert(`Sorting by: ${sortSelect.value}`);
            // Later, this will sort real flight data dynamically
        });
    }

    // Example: simulate empty result message
    const noFlights = document.getElementById('no-flights');
    if (noFlights && flightsContainer.children.length <= 1) {
        noFlights.style.display = "block";
    }
});