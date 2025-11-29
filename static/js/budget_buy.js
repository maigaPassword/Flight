// ============================================
// Budget Buy - Interactive JavaScript
// ============================================

console.log('🎯 Budget Buy JS loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOMContentLoaded - Initializing...');
    initializeBudgetSlider();
    initializeFormValidation();
    initializeToggleLogic();
    initializeModeSelection();
    setupFormSubmission();
    
    // Auto-refresh status every 30 seconds
    setInterval(refreshRequestStatus, 30000);
});

// ============================================
// Budget Range Slider (Updated for Tailwind)
// ============================================
function initializeBudgetSlider() {
    const minSlider = document.getElementById('min_budget');
    const maxSlider = document.getElementById('max_budget');
    const minInput = document.getElementById('min_budget_input');
    const maxInput = document.getElementById('max_budget_input');
    const minDisplay = document.getElementById('minBudgetDisplay');
    const maxDisplay = document.getElementById('maxBudgetDisplay');
    const sliderRange = document.getElementById('sliderRange');
    
    if (!minSlider || !maxSlider) return;
    
    // Enable pointer events for sliders
    minSlider.style.pointerEvents = 'all';
    maxSlider.style.pointerEvents = 'all';
    
    function updateSlider() {
        let minVal = parseInt(minSlider.value);
        let maxVal = parseInt(maxSlider.value);
        
        // Prevent crossing
        if (minVal >= maxVal) {
            minVal = maxVal - 50;
            minSlider.value = minVal;
        }
        
        // Update displays
        minDisplay.textContent = '$' + minVal;
        maxDisplay.textContent = '$' + maxVal;
        minInput.value = minVal;
        maxInput.value = maxVal;
        
        // Update visual range
        const percent1 = (minVal / maxSlider.max) * 100;
        const percent2 = (maxVal / maxSlider.max) * 100;
        sliderRange.style.left = percent1 + '%';
        sliderRange.style.width = (percent2 - percent1) + '%';
    }
    
    function updateFromInput() {
        let minVal = parseInt(minInput.value) || 0;
        let maxVal = parseInt(maxInput.value) || 5000;
        
        // Validate range
        if (minVal < 0) minVal = 0;
        if (maxVal > 5000) maxVal = 5000;
        if (minVal >= maxVal) minVal = maxVal - 50;
        
        minSlider.value = minVal;
        maxSlider.value = maxVal;
        updateSlider();
    }
    
    // Event listeners
    minSlider.addEventListener('input', updateSlider);
    maxSlider.addEventListener('input', updateSlider);
    minInput.addEventListener('change', updateFromInput);
    maxInput.addEventListener('change', updateFromInput);
    
    // Initialize
    updateSlider();
}

// ============================================
// Form Validation
// ============================================
function initializeFormValidation() {
    const originInput = document.getElementById('origin');
    const destinationInput = document.getElementById('destination');
    const departureDateInput = document.getElementById('departure_date');
    const returnDateInput = document.getElementById('return_date');
    
    // Uppercase airport codes
    if (originInput) {
        originInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }
    
    if (destinationInput) {
        destinationInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }
    
    // Set minimum date to today
    if (departureDateInput) {
        const today = new Date().toISOString().split('T')[0];
        departureDateInput.min = today;
    }
    
    // Return date must be after departure
    if (departureDateInput && returnDateInput) {
        departureDateInput.addEventListener('change', function() {
            returnDateInput.min = this.value;
            if (returnDateInput.value && returnDateInput.value < this.value) {
                returnDateInput.value = '';
            }
        });
    }
}

// ============================================
// Toggle Logic
// ============================================
function initializeToggleLogic() {
    const nonStopToggle = document.getElementById('non_stop_only');
    const maxStopsGroup = document.getElementById('maxStopsGroup');
    const maxStopsSelect = document.getElementById('max_stops');
    
    if (nonStopToggle && maxStopsSelect) {
        nonStopToggle.addEventListener('change', function() {
            if (this.checked) {
                maxStopsSelect.value = '0';
                maxStopsSelect.disabled = true;
                maxStopsGroup.style.opacity = '0.5';
            } else {
                maxStopsSelect.disabled = false;
                maxStopsGroup.style.opacity = '1';
            }
        });
    }
}

// ============================================
// Mode Selection
// ============================================
function initializeModeSelection() {
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const passportNotice = document.getElementById('passportNotice');
    
    modeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'auto_book') {
                passportNotice.style.display = 'flex';
            } else {
                passportNotice.style.display = 'none';
            }
        });
    });
    
    // Initialize
    const selectedMode = document.querySelector('input[name="mode"]:checked');
    if (selectedMode && selectedMode.value === 'auto_book') {
        passportNotice.style.display = 'flex';
    }
}

// ============================================
// Form Submission
// ============================================
function setupFormSubmission() {
    const form = document.getElementById('budgetBuyForm');
    
    if (form) {
        console.log('✅ Form found, attaching submit handler');
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('📝 Form submission intercepted');
            
            // Validate budget range
            const minBudget = parseInt(document.getElementById('min_budget').value);
            const maxBudget = parseInt(document.getElementById('max_budget').value);
            
            if (minBudget >= maxBudget) {
                showError('Maximum budget must be greater than minimum budget');
                return;
            }
            
            if (minBudget < 0 || maxBudget > 5000) {
                showError('Budget must be between $0 and $5000');
                return;
            }
            
            // Check if auto-book mode requires passport
            const mode = document.querySelector('input[name="mode"]:checked').value;
            if (mode === 'auto_book') {
                const hasPassport = await checkPassportInfo();
                if (!hasPassport) {
                    openPassportModal();
                    return;
                }
            }
            
            // Submit form
            const formData = new FormData(form);
            
            console.log('🚀 Submitting form via AJAX...');
            
            try {
                const response = await fetch('/budget-buy', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('📡 Response received:', response.status);
                
                const result = await response.json();
                console.log('📦 Result:', result);
                
                if (result.success) {
                    showSuccess('✅ Budget tracking request created successfully!');
                    form.reset();
                    
                    // Reset the budget slider display
                    document.getElementById('minBudgetDisplay').textContent = '$500';
                    document.getElementById('maxBudgetDisplay').textContent = '$1500';
                    
                    // Redirect to active requests page after 2 seconds
                    setTimeout(() => {
                        window.location.href = '/active-requests';
                    }, 2000);
                } else {
                    showError(result.message || 'Failed to submit request');
                }
            } catch (error) {
                console.error('❌ Submission error:', error);
                showError('An error occurred. Please try again.');
            }
        });
    } else {
        console.error('❌ Form not found!');
    }
}

// ============================================
// Passport Modal
// ============================================
async function checkPassportInfo() {
    try {
        const response = await fetch('/api/check-passport');
        const data = await response.json();
        return data.has_passport;
    } catch (error) {
        console.error('Error checking passport:', error);
        return false;
    }
}

function openPassportModal() {
    const modal = document.getElementById('passportModal');
    if (modal) {
        modal.checked = true;  // DaisyUI uses checkbox toggle
    }
}

function closePassportModal() {
    const modal = document.getElementById('passportModal');
    if (modal) {
        modal.checked = false;  // DaisyUI uses checkbox toggle
    }
}

// Passport form submission
const passportForm = document.getElementById('passportForm');
if (passportForm) {
    passportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/api/save-passport', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                closePassportModal();
                showSuccess('Passport information saved!');
                // Resubmit main form
                document.getElementById('budgetBuyForm').dispatchEvent(new Event('submit'));
            } else {
                showError(result.message || 'Failed to save passport information');
            }
        } catch (error) {
            console.error('Passport save error:', error);
            showError('An error occurred. Please try again.');
        }
    });
}

// ============================================
// Cancel Request
// ============================================
async function cancelRequest(requestId) {
    if (!confirm('Are you sure you want to cancel this request?')) {
        return;
    }
    
    try {
        const response = await fetch(`/budget-buy/cancel/${requestId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Request cancelled successfully');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showError(result.message || 'Failed to cancel request');
        }
    } catch (error) {
        console.error('Cancel error:', error);
        showError('An error occurred. Please try again.');
    }
}

// ============================================
// Check Now - Manual Price Check
// ============================================
async function checkNow(requestId) {
    showLoading();
    
    try {
        const response = await fetch(`/budget-buy/check-now/${requestId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.success) {
            if (result.booked) {
                // Flight was booked!
                showSuccess(`🎉 Flight Booked Successfully!\n\n${result.message}`);
                
                // Reload after 3 seconds to show booked status
                setTimeout(() => {
                    window.location.reload();
                }, 3000);
            } else if (result.in_budget) {
                // In budget but not booked (alert-only mode)
                showSuccess(`✅ ${result.message}\n💰 Best Price: $${result.price.toFixed(2)}`);
                
                // Reload after 2 seconds
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                // Not in budget yet
                showError(`⏳ ${result.message}\n💰 Current Price: $${result.price.toFixed(2)}\n🎯 Your Budget: $${result.min_budget} - $${result.max_budget}`);
            }
        } else {
            if (result.needs_passport) {
                if (confirm(result.message + '\n\nWould you like to add your passport details now?')) {
                    openPassportModal();
                }
            } else {
                showError(result.message || 'Failed to check prices');
            }
        }
    } catch (error) {
        hideLoading();
        console.error('Check now error:', error);
        showError('An error occurred while checking prices. Please try again.');
    }
}

// ============================================
// Status Refresh
// ============================================
async function refreshRequestStatus() {
    try {
        const response = await fetch('/budget-buy/status');
        const data = await response.json();
        
        if (data.requests) {
            updateRequestsTable(data.requests);
        }
    } catch (error) {
        console.error('Status refresh error:', error);
    }
}

function updateRequestsTable(requests) {
    const container = document.getElementById('requestsContainer');
    if (!container) return;
    
    // Only update if there are changes
    const currentRows = document.querySelectorAll('.request-row');
    if (currentRows.length === 0 && requests.length === 0) return;
    
    // Simple reload for now - could be optimized with DOM manipulation
    if (requests.length > 0) {
        location.reload();
    }
}

// ============================================
// Notifications
// ============================================
function showSuccess(message) {
    const toast = document.getElementById('successMessage');
    const text = document.getElementById('successText');
    
    if (toast && text) {
        text.textContent = message;
        toast.style.display = 'block';
        
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    } else {
        // Fallback if toast element doesn't exist
        alert(message);
    }
}

function showError(message) {
    // Create a temporary error toast
    const errorDiv = document.createElement('div');
    errorDiv.className = 'toast toast-top toast-end';
    errorDiv.innerHTML = `
        <div class="alert alert-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

// ============================================
// Utility Functions
// ============================================
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }).format(date);
}

// ============================================
// Loading Animation
// ============================================
function showLoading() {
    // Could add a loading overlay
    document.body.style.cursor = 'wait';
}

function hideLoading() {
    document.body.style.cursor = 'default';
}

// Make functions available globally
window.cancelRequest = cancelRequest;
window.checkNow = checkNow;
window.closePassportModal = closePassportModal;
window.openPassportModal = openPassportModal;
