/**
 * Flight Booking System - Frontend JavaScript
 * ============================================
 * Handles all client-side interactions including:
 * - Burger menu navigation (mobile)
 * - Trip type toggle (one-way vs round-trip)
 * - Flight card population and display
 * - Flight details modal (show more popup)
 * - Cabin class selection
 * - Date slider for alternate dates
 * - Airport autocomplete search
 * - Roundtrip flight selection flow
 * - Popular destinations interaction
 * 
 * Author: Group 5
 * Date: 2025
 */

console.log("Skyvela frontend connected successfully!");


// ========================DOMContentLoaded Wrapper===========================
// All DOM-dependent code runs after page is fully loaded

document.addEventListener("DOMContentLoaded", () => {
    
    // ===== Burger Menu Toggle =====
    // Handles mobile navigation menu open/close
    const burgerMenu = document.querySelector('.burger-menu');
    const navLinks = document.querySelector('.nav-links');
    
    if (burgerMenu && navLinks) {
        // Toggle menu on burger button click
        burgerMenu.addEventListener('click', () => {
            burgerMenu.classList.toggle('active');
            navLinks.classList.toggle('active');
            
            // Update ARIA attribute for accessibility
            const isExpanded = navLinks.classList.contains('active');
            burgerMenu.setAttribute('aria-expanded', isExpanded);
        });
        
        // Close menu when clicking on any navigation link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                burgerMenu.classList.remove('active');
                navLinks.classList.remove('active');
                burgerMenu.setAttribute('aria-expanded', 'false');
            });
        });
        
        // Close menu when clicking outside of navigation area
        document.addEventListener('click', (e) => {
            if (!burgerMenu.contains(e.target) && !navLinks.contains(e.target)) {
                burgerMenu.classList.remove('active');
                navLinks.classList.remove('active');
                burgerMenu.setAttribute('aria-expanded', 'false');
            }
        });
    }
    
    // Safe airports map - prevents errors if AIRPORTS data isn't loaded
    const airportsMap = (typeof AIRPORTS !== 'undefined' ? AIRPORTS : (window.AIRPORTS || {}));
    
    // ===== Trip type toggle (show/hide return date) =====
    // Dynamically shows/hides return date field based on trip type selection
    const tripTypeRadios = document.querySelectorAll('input[name="trip_type"]');
    const returnWrap = document.getElementById("return-date-wrapper");
    
    console.log('Trip type radios found:', tripTypeRadios.length); // Debug
    console.log('Return wrapper found:', returnWrap); // Debug
    
    if (tripTypeRadios.length > 0 && returnWrap) {
        const toggleReturn = () => {
            const selectedType = document.querySelector('input[name="trip_type"]:checked')?.value;
            console.log('Trip type changed to:', selectedType); // Debug log
            if (selectedType === 'roundtrip') {
                returnWrap.classList.add('visible'); // Add visible class
                console.log('Added visible class, classes:', returnWrap.className); // Debug
                const retInput = document.getElementById('return_date');
                if (retInput) retInput.required = true;
                console.log('Return date field shown'); // Debug log
            } else {
                returnWrap.classList.remove('visible'); // Remove visible class
                console.log('Removed visible class, classes:', returnWrap.className); // Debug
                const retInput = document.getElementById('return_date');
                if (retInput) retInput.required = false;
                console.log('Return date field hidden'); // Debug log
            }
        };
        
        tripTypeRadios.forEach(radio => {
            radio.addEventListener('change', toggleReturn);
            console.log('Added change listener to radio:', radio.id); // Debug
        });
        
        toggleReturn(); // Initial state
        console.log('Initial toggle complete'); // Debug
    } else {
        console.error('Trip type toggle not initialized:', {
            radiosFound: tripTypeRadios.length,
            wrapperFound: !!returnWrap
        });
    }
    
    // ===== Set minimum dates for date inputs =====
    const today = new Date().toISOString().split('T')[0];
    const departureInput = document.getElementById('date');
    const returnInput = document.getElementById('return_date');
    
    if (departureInput) {
        departureInput.setAttribute('min', today);
        console.log('Departure date input found and min date set to:', today);
    }
    
    if (returnInput) {
        returnInput.setAttribute('min', today);
        console.log('Return date input found and min date set to:', today);
        
        // When departure date changes, update return date minimum
        if (departureInput) {
            departureInput.addEventListener('change', function() {
                returnInput.setAttribute('min', this.value || today);
            });
        }
    }
    
    // Fallback for old select-based trip type (if exists on other pages)
    const tripTypeEl = document.getElementById("trip_type");
    if (tripTypeEl && returnWrap && !tripTypeRadios.length) {
        const toggleReturn = () => {
            if (tripTypeEl.value === 'roundtrip') {
                returnWrap.style.display = 'block';
                const retInput = document.getElementById('return_date');
                if (retInput) retInput.required = true;
            } else {
                returnWrap.style.display = 'none';
                const retInput = document.getElementById('return_date');
                if (retInput) retInput.required = false;
            }
        };
        tripTypeEl.addEventListener('change', toggleReturn);
        toggleReturn();
    }
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
    function formatTime(dateObj) {
        try {
            let h = dateObj.getHours();
            const m = dateObj.getMinutes();
            const am = h < 12;
            h = h % 12; if (h === 0) h = 12;
            const hh = String(h).padStart(2, '0');
            const mm = String(m).padStart(2, '0');
            return `${hh}:${mm} ${am ? 'AM' : 'PM'}`;
        } catch (e) {
            return '';
        }
    }
    document.querySelectorAll(".flight-card").forEach(card => {
        // --- Route Info ---
        const routeP = card.querySelector(".route");
        const originCode = routeP?.dataset.origin;
        const destCode = routeP?.dataset.destination;
                if (routeP && originCode && destCode){
                    const originCity = airportsMap[originCode]?.city || originCode;
                    const destCity = airportsMap[destCode]?.city || destCode;
          routeP.innerHTML = `<span style="color:#00c8ff;">From:</span> ${originCity} (${originCode}) 
                              <span style="color:#00c8ff;">To:</span> ${destCity} (${destCode})`;
        }

        // --- Stops Info ---
        const stopsP = card.querySelector(".stops");
        let segments = [];
        try {
            segments = card.dataset.segments ? JSON.parse(card.dataset.segments) : [];
        } catch(e){
            segments = [];
        }
        const stopSegments = segments.slice(0, -1);

        if (stopsP && stopSegments.length > 0) {
            const stopsList = stopSegments.map(seg => 
                `${seg.destination}, ${airportsMap[seg.destination]?.city || seg.destination}`
            ).join("; ");
            // Replace text to avoid duplicate like "2 stops: 2 stops"
            stopsP.innerHTML = `<strong>Stops:</strong> ${stopSegments.length} stop${stopSegments.length > 1 ? 's' : ''} (${stopsList})`;
        }

        // Remove small details row (times) for a cleaner card UI
        const existingDetails = card.querySelector('.details-row');
        if (existingDetails) existingDetails.remove();
    });

    //======================= Flight "Show More" Popup ===========================
    let currentModalContext = null; // { leg: 'outbound'|'return'|'oneway', flightData, cardEl }
    document.querySelectorAll(".show-more-btn").forEach(btn => {
    btn.addEventListener("click", e => {
        const card = e.target.closest(".flight-card");
        if (!card) return;

        const flightData = JSON.parse(card.dataset.flight || "{}");
        if (!flightData) return;

                const isOutbound = card.classList.contains('outbound-card');
                const isReturn = card.classList.contains('return-card');
                // Prefer class-based detection; fallback to trip_type
                let leg = 'oneway';
                if (isReturn) leg = 'return';
                else if (isOutbound) leg = 'outbound';
                else {
                    const tripType = (document.getElementById('trip_type')?.value) || 'oneway';
                    leg = tripType === 'roundtrip' ? 'outbound' : 'oneway';
                }
        currentModalContext = { leg, flightData, cardEl: card };

        const depTime = new Date(flightData.departure);
        const arrTime = new Date(flightData.arrival);
        const duration = flightData.duration;
        const stops = flightData.stops_text || "Nonstop";

        const airline = flightData.airline_name;
        const logo = flightData.airline_logo;
        const origin = flightData.origin;
        const destination = flightData.destination;

        function formatTime(dateObj) {
            try {
                let h = dateObj.getHours();
                const m = dateObj.getMinutes();
                const am = h < 12;
                h = h % 12; if (h === 0) h = 12;
                const hh = String(h).padStart(2, '0');
                const mm = String(m).padStart(2, '0');
                return `${hh}:${mm} ${am ? 'AM' : 'PM'}`;
            } catch (e) {
                return '';
            }
        }

        // Build modal HTML
        let html = `
        <div class="flight-popup-header">
            ${logo ? `<img src="${logo}" class="popup-logo" alt="${airline}">` : ""}
            <div class="airline-info">
                <h2>${airline}</h2>
                <p>WiFi, entertainment and power on this flight</p>
            </div>
        </div>

        <div class="flight-details">
            <div class="detail-item"><strong>Route:</strong> ${origin} → ${destination}</div>
            <div class="detail-item"><strong>Time:</strong> ${formatTime(depTime)} - ${formatTime(arrTime)}</div>
            <div class="detail-item"><strong>Duration:</strong> ${duration}</div>
            <div class="detail-item"><strong>Stops:</strong> ${stops}</div>
        </div>
        `;

        // Add fares by cabin
        const faresByCabin = flightData.fares_by_cabin || {};
        const cabinOrder = ["ECONOMY", "BUSINESS", "FIRST"];
        html += `<div class="fare-options-container">`;
        cabinOrder.forEach(cabin => {
            const fares = faresByCabin[cabin];
            if (!fares) return;
            const fare = fares[0];

            let bagText = "No checked bags included";
            if (fare.bags.quantity) {
                bagText = `${fare.bags.quantity} checked bag(s)${fare.bags.weight ? `, ${fare.bags.weight}${fare.bags.type || 'kg'}` : ""}`;
            }

            html += `
            <div class="cabin-column">
                <h3 class="section-title">${cabin}</h3>
                <div class="fare-option">
                    <h4>${fare.fare_type}</h4>
                    <div class="price">$${fare.price.toFixed(2)} 
                        <span style="font-size:13px;color:#aaa;">per traveler</span>
                    </div>
                    <div class="features">
                        <span><strong>Seat:</strong> ${String(fare.seat||'').includes("Not") ? "Seat choice not allowed" : "Seat choice included"}</span>
                        <span><strong>Bags:</strong> Personal item, Carry-on, ${bagText}</span>
                        <span><strong>Flexibility:</strong> ${fare.flexibility}</span>
                        <span><strong>Change:</strong> ${fare.change_fee || "Changes included"}</span>
                    </div>
                    <button class="select-flight-btn" 
                            data-cabin="${cabin}" 
                            data-fare="${(fare.fare_type||'').replace(/"/g,'%22')}" 
                            data-price="${fare.price}">
                        Select ${cabin}
                    </button>
                </div>
            </div>
            `;
        });
        html += `</div>`;

        if (!modal || !modalBody) {
            // If modal not present (e.g., on select_return), create it dynamically
            const m = document.createElement('div');
            m.id = 'flightModal';
            m.className = 'flight-modal';
            m.innerHTML = `<div class="flight-modal-content"><span class="flight-close-btn">&times;</span><div id="flightModalBody"></div></div>`;
            document.body.appendChild(m);
            const close = m.querySelector('.flight-close-btn');
            if (close) close.addEventListener('click', ()=> m.style.display='none');
            m.style.display = 'flex';
            const mb = m.querySelector('#flightModalBody');
            mb.innerHTML = html;
        } else {
            modalBody.innerHTML = html;
            modal.style.display = "flex";
        }

        // Handle select flight buttons
    (document.getElementById('flightModalBody') || modalBody).querySelectorAll(".select-flight-btn").forEach(selectBtn => {
            selectBtn.addEventListener("click", () => {
                try {
                    const cabinValue = selectBtn.dataset.cabin || 'ECONOMY';
                    if (currentModalContext && currentModalContext.leg === 'outbound') {
                        // Build and submit a POST to /select_return with outbound selection
                        const container = document.getElementById('date-slider-container');
                        const origin = container?.dataset.origin || '';
                        const destination = container?.dataset.destination || '';
                        const returnDate = container?.dataset.returnDate || '';

                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = '/select_return';
                        const add = (n,v)=>{ const i=document.createElement('input'); i.type='hidden'; i.name=n; i.value=v; form.appendChild(i); };
                        add('outbound_json', JSON.stringify(flightData));
                        add('cabin_out', cabinValue);
                        add('origin', origin);
                        add('destination', destination);
                        add('return_date', returnDate);
                        document.body.appendChild(form);
                        form.submit();
                        return;
                    }
                    if (currentModalContext && currentModalContext.leg === 'return') {
                        // Submit to /flight_summary with outbound from page context and chosen return cabin
                        const ctx = window.__SELECT_RETURN_CTX__ || {};
                        const retForm = document.getElementById('ret-summary-form');
                        if (retForm) {
                            document.getElementById('ret_return_json').value = JSON.stringify(flightData);
                            document.getElementById('ret_cabin_ret').value = cabinValue;
                            retForm.submit();
                            return;
                        }
                    }

                    // Fallback: One-way flow -> POST to /flight_summary (outbound only)
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = '/flight_summary';
                    const addHidden = (name, value) => {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = name;
                        input.value = value;
                        form.appendChild(input);
                    };
                    addHidden('outbound_json', JSON.stringify(flightData));
                    addHidden('cabin_out', cabinValue || 'ECONOMY');
                    document.body.appendChild(form);
                    form.submit();
                } catch (err) {
                    console.error("Error processing flight selection:", err);
                    alert("Something went wrong while selecting your flight. Please try again.");
                }
            });
        });
    });

    // =====================Date Slider / Day Buttons ===========================
    
    const container = document.getElementById("date-slider-container");
    if (container) {
        const dateButtons = container.querySelectorAll(".date-btn");
        dateButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                dateButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                const selectedDate = btn.dataset.date;
                const origin = container.dataset.origin;
                const destination = container.dataset.destination;
                const tripType = container.dataset.tripType || 'oneway';
                const returnDate = container.dataset.returnDate || '';

                if (origin && destination) {
                    const params = new URLSearchParams({ origin, destination, date: selectedDate, trip_type: tripType });
                    if (tripType === 'roundtrip' && returnDate) params.set('return_date', returnDate);
                    window.location.href = `/search?${params.toString()}`;
                }
            });
        });

        // --- Optional: Scroll Arrows ---
        const prevBtn = document.getElementById("prev-date");
        const nextBtn = document.getElementById("next-date");
        prevBtn?.addEventListener("click", () => container.scrollBy({ left: -150, behavior: "smooth" }));
        nextBtn?.addEventListener("click", () => container.scrollBy({ left: 150, behavior: "smooth" }));
    }
    
    // ===== Popular Destinations Click Handler =====
    document.querySelectorAll('.destination-card').forEach(card => {
        card.addEventListener('click', function() {
            const destination = this.dataset.destination;
            const destinationName = this.querySelector('.destination-location h3').textContent;
            const country = this.querySelector('.destination-location p').textContent;
            
            // Scroll to hero section
            const heroSection = document.querySelector('.hero');
            if (heroSection) {
                heroSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            
            // Fill in the destination field
            setTimeout(() => {
                const destInput = document.getElementById('destination');
                const destCode = document.getElementById('destination_code');
                
                if (destInput && destCode) {
                    destInput.value = `${destinationName} (${destination})`;
                    destCode.value = destination;
                    
                    // Focus on origin field to encourage user to enter their location
                    const originInput = document.getElementById('origin');
                    if (originInput) {
                        originInput.focus();
                    }
                }
            }, 800);
        });
    });
});



// ==========================Airport Autocomplete==================

let airports = [];
if (typeof AIRPORTS !== 'undefined') {
  airports = Object.entries(AIRPORTS).map(([iata, info]) => {
      return {
          iata,
          city: info.city,
          name: info.name,
          label: `${info.city} - ${info.name} (${iata})`
      };
  });
}

function setupAutocomplete(inputId, hiddenId) {
    const input = document.getElementById(inputId);
    const hidden = document.getElementById(hiddenId);
    if (!input || !hidden || airports.length === 0) return;

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

// Initialize for both inputs (only if AIRPORTS present)
setupAutocomplete('origin', 'origin_code');
setupAutocomplete('destination', 'destination_code');


// ======================= Roundtrip selection flow =========================
(function(){
    const tripTypeEl = document.getElementById('trip_type');
    if (!tripTypeEl || tripTypeEl.value !== 'roundtrip') return;

    const outboundList = document.getElementById('outbound-list');
    const returnSection = document.getElementById('return-section');
    const returnList = document.getElementById('return-list');
    const summaryForm = document.getElementById('summary-form');
    if (!outboundList || !returnSection || !summaryForm) return;

        let selectedOutbound = null;
        let selectedReturn = null;
        let selectedOutboundCabin = null;
        let selectedReturnCabin = null;

        // expose for modal callbacks
        window.updateRoundtripSummary = updateSummary;
        Object.defineProperties(window, {
            __selectedOutbound: {
                set(v){ selectedOutbound = v; }, get(){ return selectedOutbound; }
            },
            __selectedReturn: {
                set(v){ selectedReturn = v; }, get(){ return selectedReturn; }
            },
            __selectedOutboundCabin: {
                set(v){ selectedOutboundCabin = v; }, get(){ return selectedOutboundCabin; }
            },
            __selectedReturnCabin: {
                set(v){ selectedReturnCabin = v; }, get(){ return selectedReturnCabin; }
            }
        });

        function getMinFarePrice(flight){
        try {
            const fbc = flight.fares_by_cabin || {};
            let min = Infinity;
            for (const cabin of Object.keys(fbc)){
                const fares = fbc[cabin];
                if (fares && fares.length){
                    const p = Number(fares[0].price || fares[0].total || 0);
                    if (!isNaN(p) && p < min) min = p;
                }
            }
            return min !== Infinity ? min : 0;
        } catch { return 0; }
    }

        function getPriceForCabin(flight, cabin){
            try{
                const fares = (flight.fares_by_cabin || {})[cabin];
                if (fares && fares.length){
                    const p = Number(fares[0].price || fares[0].total || 0);
                    return isNaN(p) ? 0 : p;
                }
                return null;
            } catch { return null; }
        }

        function updateSummary(){
            if (!selectedOutbound || !selectedReturn) return;
            let outPrice = null;
            let retPrice = null;
            if (selectedOutboundCabin) outPrice = getPriceForCabin(selectedOutbound, selectedOutboundCabin);
            if (selectedReturnCabin) retPrice = getPriceForCabin(selectedReturn, selectedReturnCabin);
            if (outPrice === null) outPrice = getMinFarePrice(selectedOutbound);
            if (retPrice === null) retPrice = getMinFarePrice(selectedReturn);
        const total = (outPrice + retPrice).toFixed(2);

    const outCityA = airportsMap[selectedOutbound.origin]?.city || selectedOutbound.origin;
    const outCityB = airportsMap[selectedOutbound.destination]?.city || selectedOutbound.destination;
    const retCityA = airportsMap[selectedReturn.origin]?.city || selectedReturn.origin;
    const retCityB = airportsMap[selectedReturn.destination]?.city || selectedReturn.destination;

            const outCabinText = selectedOutboundCabin ? ` • ${selectedOutboundCabin}` : '';
            const retCabinText = selectedReturnCabin ? ` • ${selectedReturnCabin}` : '';
            document.getElementById('summary-out').textContent = `Outbound: ${outCityA} (${selectedOutbound.origin}) → ${outCityB} (${selectedOutbound.destination})${outCabinText} — $${outPrice.toFixed(2)}`;
            document.getElementById('summary-ret').textContent = `Return: ${retCityA} (${selectedReturn.origin}) → ${retCityB} (${selectedReturn.destination})${retCabinText} — $${retPrice.toFixed(2)}`;
        document.getElementById('summary-total').textContent = `$${total}`;

        document.getElementById('outbound_json').value = JSON.stringify(selectedOutbound);
        document.getElementById('return_json').value = JSON.stringify(selectedReturn);
            if (selectedOutboundCabin) document.getElementById('cabin_out').value = selectedOutboundCabin;
            if (selectedReturnCabin) document.getElementById('cabin_ret').value = selectedReturnCabin;
        summaryForm.style.display = 'block';
    }

    // Handle outbound selection
    outboundList.querySelectorAll('.select-outbound-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.flight-card');
            if (!card) return;
            // Clear previous selection styling
            outboundList.querySelectorAll('.flight-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');

            try {
                selectedOutbound = JSON.parse(card.dataset.flight || '{}');
            } catch { selectedOutbound = null; }

                // Choose default cabin if not set
                if (!selectedOutboundCabin){
                    const fbc = selectedOutbound?.fares_by_cabin || {};
                    selectedOutboundCabin = ['ECONOMY','BUSINESS','FIRST'].find(c => fbc[c] && fbc[c].length) || null;
                }

            // Reveal return section
            returnSection.style.display = 'block';
                returnSection.scrollIntoView({behavior:'smooth', block:'start'});
            // Reset previous return selection
            selectedReturn = null;
                selectedReturnCabin = null;
            if (returnList) returnList.querySelectorAll('.flight-card').forEach(c => c.classList.remove('selected'));
            summaryForm.style.display = 'none';
        });
    });

    // Handle return selection
    if (returnList){
        returnList.querySelectorAll('.select-return-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const card = e.target.closest('.flight-card');
                if (!card) return;
                returnList.querySelectorAll('.flight-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                try {
                    selectedReturn = JSON.parse(card.dataset.flight || '{}');
                } catch { selectedReturn = null; }
                        // Choose default cabin if not set
                        if (!selectedReturnCabin){
                            const fbc = selectedReturn?.fares_by_cabin || {};
                            selectedReturnCabin = ['ECONOMY','BUSINESS','FIRST'].find(c => fbc[c] && fbc[c].length) || null;
                        }
                updateSummary();
            });
        });
    }
})();


// ======================== Enhanced Airport Autocomplete ===========================
// Provides real-time airport search suggestions with support for:
// - City names (e.g., "Paris", "New York")
// - Airport names (e.g., "Charles de Gaulle", "JFK International")
// - IATA codes (e.g., "CDG", "JFK")

(function() {
    // Load airports data from global AIRPORTS object
    const airportsData = typeof AIRPORTS !== 'undefined' ? AIRPORTS : (window.AIRPORTS || {});
    const airportsList = Object.entries(airportsData).map(([iata, info]) => ({
        iata: iata,
        name: info.name || '',
        city: info.city || '',
        country: info.country || '',
        state: info.state || ''
    }));

    console.log('🔍 Airport Autocomplete initialized with', airportsList.length, 'airports');
    if (airportsList.length === 0) {
        console.warn('⚠️ No airports data loaded! AIRPORTS object:', airportsData);
    }

    /**
     * Search airports by keyword (city, name, or code)
     * @param {string} keyword - Search term
     * @returns {Array} - Matching airports
     */
    function searchAirports(keyword) {
        if (!keyword || keyword.length < 2) return [];
        
        const searchTerm = keyword.toLowerCase().trim();
        
        // Search across IATA code, city, and airport name
        const matches = airportsList.filter(airport => {
            const iataMatch = airport.iata.toLowerCase().includes(searchTerm);
            const cityMatch = airport.city.toLowerCase().includes(searchTerm);
            const nameMatch = airport.name.toLowerCase().includes(searchTerm);
            
            return iataMatch || cityMatch || nameMatch;
        });
        
        // Prioritize exact matches and major airports
        return matches
            .sort((a, b) => {
                // Exact IATA code match gets highest priority
                const aExactCode = a.iata.toLowerCase() === searchTerm;
                const bExactCode = b.iata.toLowerCase() === searchTerm;
                if (aExactCode && !bExactCode) return -1;
                if (!aExactCode && bExactCode) return 1;
                
                // Exact city match gets second priority
                const aExactCity = a.city.toLowerCase() === searchTerm;
                const bExactCity = b.city.toLowerCase() === searchTerm;
                if (aExactCity && !bExactCity) return -1;
                if (!aExactCity && bExactCity) return 1;
                
                // Otherwise sort alphabetically by city
                return a.city.localeCompare(b.city);
            })
            .slice(0, 8); // Limit to 8 results
    }

    /**
     * Highlight matching text in results
     * @param {string} text - Text to highlight
     * @param {string} keyword - Search keyword
     * @returns {string} - HTML with highlighted matches
     */
    function highlightMatch(text, keyword) {
        if (!text || !keyword) return text;
        const regex = new RegExp(`(${keyword})`, 'gi');
        return text.replace(regex, '<span style="color: #48cae4; font-weight: 700;">$1</span>');
    }

    /**
     * Setup autocomplete for an input field
     * @param {string} inputId - ID of the input element
     */
    function setupAirportAutocomplete(inputId) {
        const input = document.getElementById(inputId);
        if (!input) {
            console.warn(`⚠️ Input field #${inputId} not found!`);
            return;
        }
        
        console.log(`✅ Setting up autocomplete for #${inputId}`);
        
        // Create autocomplete dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            background: linear-gradient(135deg, rgba(3, 4, 94, 0.98) 0%, rgba(2, 62, 138, 0.98) 100%);
            border: 2px solid rgba(72, 202, 228, 0.4);
            border-radius: 12px;
            margin-top: 8px;
            max-height: 380px;
            overflow-y: auto;
            display: none;
            z-index: 1000;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(72, 202, 228, 0.1);
            backdrop-filter: blur(10px);
        `;
        
        // Custom scrollbar styling
        const style = document.createElement('style');
        style.textContent = `
            .autocomplete-dropdown::-webkit-scrollbar {
                width: 8px;
            }
            .autocomplete-dropdown::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
            }
            .autocomplete-dropdown::-webkit-scrollbar-thumb {
                background: rgba(72, 202, 228, 0.4);
                border-radius: 10px;
            }
            .autocomplete-dropdown::-webkit-scrollbar-thumb:hover {
                background: rgba(72, 202, 228, 0.6);
            }
        `;
        document.head.appendChild(style);
        
        // Insert dropdown after input
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(dropdown);
        
        let debounceTimer;
        let currentFocus = -1;
        
        // Handle input changes
        input.addEventListener('input', function() {
            const keyword = this.value.trim();
            console.log(`📝 Input detected in #${inputId}: "${keyword}"`);
            currentFocus = -1;
            
            clearTimeout(debounceTimer);
            
            if (keyword.length < 2) {
                console.log('⚠️ Keyword too short, need at least 2 characters');
                dropdown.style.display = 'none';
                return;
            }
            
            // Debounce for smooth performance
            debounceTimer = setTimeout(() => {
                const results = searchAirports(keyword);
                console.log(`🔍 Search results for "${keyword}":`, results.length, 'airports found');
                dropdown.innerHTML = '';
                
                if (results.length === 0) {
                    // Show "no results" message
                    const noResults = document.createElement('div');
                    noResults.style.cssText = `
                        padding: 20px;
                        text-align: center;
                        color: rgba(173, 232, 244, 0.6);
                        font-size: 0.9rem;
                    `;
                    noResults.innerHTML = `
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 8px;">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                        <div>No airports found for "${keyword}"</div>
                    `;
                    dropdown.appendChild(noResults);
                    dropdown.style.display = 'block';
                    dropdown.style.width = input.offsetWidth + 'px';
                    return;
                }
                
                results.forEach((airport, index) => {
                    const item = document.createElement('div');
                    item.className = 'autocomplete-item';
                    item.dataset.iata = airport.iata;
                    item.style.cssText = `
                        padding: 14px 18px;
                        cursor: pointer;
                        color: #fff;
                        border-bottom: 1px solid rgba(72, 202, 228, 0.15);
                        transition: all 0.2s ease;
                        display: flex;
                        align-items: center;
                        gap: 12px;
                    `;
                    
                    // Create location string
                    let location = airport.city;
                    if (airport.state && airport.country === 'US') {
                        location += `, ${airport.state}`;
                    } else if (airport.country) {
                        location += `, ${airport.country}`;
                    }
                    
                    item.innerHTML = `
                        <div style="
                            background: linear-gradient(135deg, rgba(72, 202, 228, 0.2), rgba(0, 180, 216, 0.2));
                            border: 1.5px solid rgba(72, 202, 228, 0.4);
                            border-radius: 8px;
                            padding: 8px 12px;
                            font-weight: 700;
                            font-size: 0.95rem;
                            color: #48cae4;
                            min-width: 50px;
                            text-align: center;
                            box-shadow: 0 2px 8px rgba(72, 202, 228, 0.2);
                        ">
                            ${highlightMatch(airport.iata, keyword)}
                        </div>
                        <div style="flex: 1; min-width: 0;">
                            <div style="
                                font-weight: 600;
                                font-size: 0.95rem;
                                color: #fff;
                                margin-bottom: 3px;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            ">
                                ${highlightMatch(location, keyword)}
                            </div>
                            <div style="
                                font-size: 0.8rem;
                                color: rgba(173, 232, 244, 0.7);
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            ">
                                ${highlightMatch(airport.name, keyword)}
                            </div>
                        </div>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(72, 202, 228, 0.5)" stroke-width="2">
                            <path d="M9 18l6-6-6-6"/>
                        </svg>
                    `;
                    
                    // Remove last border
                    if (index === results.length - 1) {
                        item.style.borderBottom = 'none';
                    }
                    
                    // Hover effect
                    item.addEventListener('mouseenter', function() {
                        this.style.background = 'rgba(72, 202, 228, 0.15)';
                        this.style.transform = 'translateX(4px)';
                        this.style.borderLeftColor = '#48cae4';
                        this.style.borderLeft = '3px solid #48cae4';
                        this.style.paddingLeft = '15px';
                    });
                    item.addEventListener('mouseleave', function() {
                        this.style.background = 'transparent';
                        this.style.transform = 'translateX(0)';
                        this.style.borderLeft = 'none';
                        this.style.paddingLeft = '18px';
                    });
                    
                    // Click to select
                    item.addEventListener('click', function() {
                        input.value = this.dataset.iata;
                        dropdown.style.display = 'none';
                        
                        // Trigger change event for form validation
                        const event = new Event('change', { bubbles: true });
                        input.dispatchEvent(event);
                    });
                    
                    dropdown.appendChild(item);
                });
                
                dropdown.style.display = 'block';
                dropdown.style.width = input.offsetWidth + 'px';
            }, 250); // 250ms debounce
        });
        
        // Keyboard navigation
        input.addEventListener('keydown', function(e) {
            const items = dropdown.querySelectorAll('.autocomplete-item');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentFocus++;
                if (currentFocus >= items.length) currentFocus = 0;
                setActive(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentFocus--;
                if (currentFocus < 0) currentFocus = items.length - 1;
                setActive(items);
            } else if (e.key === 'Enter') {
                if (currentFocus > -1 && items[currentFocus]) {
                    e.preventDefault();
                    items[currentFocus].click();
                }
            } else if (e.key === 'Escape') {
                dropdown.style.display = 'none';
                currentFocus = -1;
            }
        });
        
        function setActive(items) {
            items.forEach((item, index) => {
                if (index === currentFocus) {
                    item.style.background = 'rgba(72, 202, 228, 0.25)';
                    item.style.transform = 'translateX(4px)';
                    item.style.borderLeft = '3px solid #48cae4';
                    item.style.paddingLeft = '15px';
                    item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                } else {
                    item.style.background = 'transparent';
                    item.style.transform = 'translateX(0)';
                    item.style.borderLeft = 'none';
                    item.style.paddingLeft = '18px';
                }
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
                currentFocus = -1;
            }
        });
        
        // Show dropdown on focus if there's existing text
        input.addEventListener('focus', function() {
            if (this.value.trim().length >= 2) {
                const event = new Event('input', { bubbles: true });
                this.dispatchEvent(event);
            }
        });
    }
    
    // Initialize autocomplete for origin and destination fields
    console.log('🎯 Initializing autocomplete for origin and destination fields...');
    setupAirportAutocomplete('origin');
    setupAirportAutocomplete('destination');
    console.log('✅ Autocomplete setup complete');
})();



