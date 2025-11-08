console.log("Skyvela frontend connected successfully!");


// ========================DOMContentLoaded Wrapper======================

document.addEventListener("DOMContentLoaded", () => {
    const sortSelect = document.getElementById("sort-options");
    const flightsContainer = document.getElementById("flights-container");
    if (sortSelect && flightsContainer) {
        sortSelect.addEventListener("change", () => {
            alert(`Sorting by: ${sortSelect.value}`);
            // TODO: implement actual sorting logic
        });
    }
    const noFlights = document.getElementById("no-flights");
    if (noFlights && (!flightsContainer || flightsContainer.children.length === 0)) {
        noFlights.style.display = "block";
    }

  
//  =======================Populate Flight Cards=======================
  
    const modal = document.getElementById("flightModal");
    const modalBody = document.getElementById("flightModalBody");
    if (!modal || !modalBody) return;
    function formatTime(dateObj) {
        return dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    document.querySelectorAll(".flight-card").forEach(card => {
        // --- Route Info ---
        const routeP = card.querySelector(".route");
        const originCode = routeP.dataset.origin;
        const destCode = routeP.dataset.destination;

        const originCity = AIRPORTS[originCode]?.city || originCode;
        const destCity = AIRPORTS[destCode]?.city || destCode;

        routeP.innerHTML = `<span style="color:#00c8ff;">From:</span> ${originCity} (${originCode}) 
                            <span style="color:#00c8ff;">To:</span> ${destCity} (${destCode})`;

        // --- Stops Info ---
        const stopsP = card.querySelector(".stops");
        const segments = card.dataset.segments ? JSON.parse(card.dataset.segments) : [];
        const stopSegments = segments.slice(0, -1);

        if (stopSegments.length > 0) {
            const stopsList = stopSegments.map(seg => 
                `${seg.destination}, ${AIRPORTS[seg.destination]?.city || seg.destination}`
            ).join("; ");
            stopsP.innerHTML += `: ${stopSegments.length} stop${stopSegments.length > 1 ? 's' : ''} (${stopsList})`;
        }

        // --- Departure & Arrival Times ---
        if (segments.length > 0) {
            const depEl = document.createElement("p");
            const arrEl = document.createElement("p");
            const dep = new Date(segments[0].departure);
            const arr = new Date(segments[segments.length - 1].arrival);

            depEl.innerHTML = `<strong>Departure:</strong> ${formatTime(dep)}`;
            arrEl.innerHTML = `<strong>Arrival:</strong> ${formatTime(arr)}`;

            const buttons = card.querySelectorAll("button");
            if (buttons.length > 0) {
                card.insertBefore(depEl, buttons[0]);
                card.insertBefore(arrEl, buttons[0]);
            }
        }
    });

 //======================= Flight "Show More" Popup===========================
      document.querySelectorAll(".show-more-btn").forEach(btn => {
        btn.addEventListener("click", e => {
            const card = e.target.closest(".flight-card");
            if (!card) return;

            const flightData = JSON.parse(card.dataset.flight || "{}");
            if (!flightData) return;

            const depTime = new Date(flightData.departure);
            const arrTime = new Date(flightData.arrival);
            const duration = flightData.duration;
            const stops = flightData.stops_text || "Nonstop";

            // --- Header Section ---
            let html = `
                <div class="flight-popup-header">
                    ${card.dataset.logo ? `<img src="${card.dataset.logo}" class="popup-logo" alt="${card.dataset.airline}">` : ""}
                    <div class="airline-info">
                        <h2>${card.dataset.airline}</h2>
                        <p>WiFi, entertainment and power on this flight</p>
                    </div>
                </div>

                <div class="flight-details">
                    <div class="detail-item"><strong>Route:</strong> ${flightData.origin} → ${flightData.destination}</div>
                    <div class="detail-item"><strong>Time:</strong> ${formatTime(depTime)} - ${formatTime(arrTime)}</div>
                    <div class="detail-item"><strong>Duration:</strong> ${duration}</div>
                    <div class="detail-item"><strong>Stops:</strong> ${stops}</div>
                </div>
            `;
            // --- Group Fares by Cabin ---
            const faresByCabin = flightData.fares_by_cabin || {};
           // --- Render Fares ---       
const cabinOrder = ["ECONOMY", "BUSINESS", "FIRST"];
html += `<div class="fare-options-container">`;
// For each cabin
cabinOrder.forEach(cabin => {
    const fares = faresByCabin[cabin];
    if (!fares) return;
    html += `<div class="cabin-column">
                <h3 class="section-title">${cabin}</h3>`;
    // show first fare
    const fare = fares[0];
    // --- Bags info from Amadeus ---
    let bagText = "No checked bags included";
    if (fare.bags.quantity) {
        if (fare.bags.weight) {
            bagText = `${fare.bags.quantity} checked bag(s), ${fare.bags.weight}${fare.bags.type || 'kg'}`;
        } else {
            bagText = `${fare.bags.quantity} checked bag(s) included`;
        }
    }
    html += `
        <div class="fare-option">
            <h4>${fare.fare_type}</h4>
            <div class="price">$${fare.price.toFixed(2)} <span style="font-size:13px;color:#aaa;">roundtrip for 1 traveler</span></div>
            <div class="features">
                <span><strong>Seat:</strong> ${fare.seat.includes("Not") ? "Seat choice not allowed" : "Seat choice included"}</span>
                <span><strong>Bags:</strong> Personal item, Carry-on, ${bagText}</span>
                <span><strong>Flexibility:</strong> ${fare.flexibility}</span>
                <span><strong>Change:</strong> ${fare.change_fee || "Changes included"}</span>
                <span><strong>WiFi:</strong> Available</span>
                <span><strong>Entertainment:</strong> Movies, Music</span>
                <span><strong>Meals:</strong> Included</span>
            </div>
            <button class="select-btn">Select</button>
        </div>
    `;
    html += `</div>`; // close cabin-column
});
html += `</div>`; // close fare-options-container
            // --- Show Modal ---
            modalBody.innerHTML = html;
            modal.style.display = "flex";
            modal.querySelector(".flight-close-btn").onclick = () => (modal.style.display = "none");
            window.onclick = e => { if (e.target === modal) modal.style.display = "none"; };
        });
    })

// =====================Date Slider / Day Buttons ===========================
  
    const container = document.getElementById("date-slider-container");
    if (!container) return;

    const dateButtons = container.querySelectorAll(".date-btn");
    dateButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            dateButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const selectedDate = btn.dataset.date;
            const origin = container.dataset.origin;
            const destination = container.dataset.destination;

            if (origin && destination) {
                window.location.href = `/search?origin=${origin}&destination=${destination}&date=${selectedDate}`;
            }
        });
    });

    // --- Optional: Scroll Arrows ---
    const prevBtn = document.getElementById("prev-date");
    const nextBtn = document.getElementById("next-date");
    prevBtn?.addEventListener("click", () => container.scrollBy({ left: -150, behavior: "smooth" }));
    nextBtn?.addEventListener("click", () => container.scrollBy({ left: 150, behavior: "smooth" }));
});



// ==========================Airport Autocomplete==================

const airports = Object.entries(AIRPORTS).map(([iata, info]) => {
    return {
        iata,
        city: info.city,
        name: info.name,
        label: `${info.city} - ${info.name} (${iata})`
    };
});

function setupAutocomplete(inputId, hiddenId) {
    const input = document.getElementById(inputId);
    const hidden = document.getElementById(hiddenId);

    const list = document.createElement('div');
    list.className = 'autocomplete-items';
    list.style.position = 'absolute';
    list.style.border = '1px solid #333';
    list.style.zIndex = '99';
    list.style.backgroundColor = '#1e1e1e';
    list.style.maxHeight = '200px';
    list.style.overflowY = 'auto';
    input.parentNode.appendChild(list);

    input.addEventListener('input', () => {
        const val = input.value.toLowerCase();
        list.innerHTML = '';
        hidden.value = '';

        if (!val) return;

        const matches = airports.filter(a =>
            a.iata.toLowerCase().includes(val) ||
            a.city.toLowerCase().includes(val) ||
            a.name.toLowerCase().includes(val)
        ).slice(0, 10); // limit 10 suggestions

        matches.forEach(a => {
            const item = document.createElement('div');
            item.innerHTML = a.label.replace(new RegExp(val, 'i'), match => `<strong>${match}</strong>`);
            item.addEventListener('click', () => {
                input.value = a.label;
                hidden.value = a.iata;
                list.innerHTML = '';
            });
            list.appendChild(item);
        });
    });

    document.addEventListener('click', (e) => {
        if (e.target !== input) list.innerHTML = '';
    });
}

// Initialize for both inputs
setupAutocomplete('origin', 'origin_code');
setupAutocomplete('destination', 'destination_code');
