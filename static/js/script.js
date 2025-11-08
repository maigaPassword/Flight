console.log("Skyvela frontend connected successfully!");

// document.addEventListener('DOMContentLoaded', () => {
//     const form = document.getElementById('flightForm');
//     if (form) {
//         form.addEventListener('submit', (e) => {
//             e.preventDefault();
//             const origin = document.getElementById('origin').value;
//             const destination = document.getElementById('destination').value;
//             const date = document.getElementById('date').value;

//             document.getElementById('results').innerHTML =
//                 `<p>Searching flights from <strong>${origin}</strong> to <strong>${destination}</strong> on <strong>${date}</strong>...</p>`;
//         });
//     }
// });

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



// ======== This is for the pop up after selecting show me more======/
document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("flightModal");
    const modalBody = document.getElementById("flightModalBody");
    const closeBtn = document.querySelector(".flight-close-btn");

    // Show More buttons
    document.querySelectorAll(".show-more-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const card = e.target.closest(".flight-card");
            const segments = JSON.parse(card.dataset.segments);

            let segmentsHtml = "";
            segments.forEach((seg, index) => {
                const dep = new Date(seg.departure);
                const arr = new Date(seg.arrival);
                segmentsHtml += `
                    <div class="segment">
                        <h4>Segment ${index + 1}</h4>
                        <p><strong>Route:</strong> ${seg.origin} → ${seg.destination}</p>
                        <p><strong>Departure:</strong> ${formatDate(dep)} at ${formatTime(dep)}</p>
                        <p><strong>Arrival:</strong> ${formatDate(arr)} at ${formatTime(arr)}</p>
                        <p><strong>Duration:</strong> ${seg.duration}</p>
                    </div>
                    <hr>
                `;
            });

            modalBody.innerHTML = `
                <div class="flight-popup-details">
                    <div class="flight-popup-header">
                        ${card.dataset.logo ? `<img src="${card.dataset.logo}" alt="${card.dataset.airline}" class="popup-logo">` : ""}
                        <h2>${card.dataset.airline}</h2>
                        <span class="flight-close-btn">&times;</span>
                    </div>
                    <p><strong>Stops:</strong> ${card.dataset.stops}</p>
                    <p><strong>Price:</strong> $${card.dataset.price}</p>
                    <p><strong>Baggage:</strong> ${card.dataset.baggage} kg</p>
                    ${segmentsHtml}
                    <button class="select-btn">Select This Flight</button>
                </div>
            `;

            modal.style.display = "flex";

            // Add event listener for the close button inside modalBody (new element)
            modalBody.querySelector(".flight-close-btn").addEventListener("click", () => {
                modal.style.display = "none";
            });
        });
    });

    // Close modal if clicking outside
    window.addEventListener("click", (e) => {
        if (e.target === modal) modal.style.display = "none";
    });
});

function formatDate(dateObj) {
    return dateObj.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatTime(dateObj) {
    return dateObj.toLocaleTimeString([], { hour: '2-digit', minute:'2-digit' });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".flight-card").forEach(card => {
        const dep = new Date(card.dataset.departure);
        const arr = new Date(card.dataset.arrival);

        const depEl = document.createElement("p");
        depEl.innerHTML = `<strong>Departure:</strong> ${formatDate(dep)} at ${formatTime(dep)}`;

        const arrEl = document.createElement("p");
        arrEl.innerHTML = `<strong>Arrival:</strong> ${formatDate(arr)} at ${formatTime(arr)}`;

        // Insert above buttons
        const buttons = card.querySelectorAll("button");
        if (buttons.length > 0) {
            card.insertBefore(depEl, buttons[0]);
            card.insertBefore(arrEl, buttons[0]);
        }
    });
});
