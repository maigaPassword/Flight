# 🔧 Autocomplete Troubleshooting Guide

## Quick Tests

### Test 1: Simple Standalone Test (NO Flask needed)
1. Open `simple_test.html` in your browser (just double-click it)
2. Type in the input field: "paris", "cdg", "new", etc.
3. You should see a dropdown with suggestions
4. Check the status message below the input

**If this works:** The autocomplete code is fine, issue is with Flask integration  
**If this doesn't work:** Browser or JavaScript issue

### Test 2: Full Test with Debug Logging
1. Start Flask: `python app.py`  
2. Open http://127.0.0.1:5000
3. Press F12 to open Developer Tools
4. Go to "Console" tab
5. Type in Origin or Destination field

**Expected console messages:**
```
✈️ Loaded 1234 airports
🔍 Airport Autocomplete initialized with 1234 airports  
🎯 Initializing autocomplete for origin and destination fields...
✅ Setting up autocomplete for #origin
✅ Setting up autocomplete for #destination
✅ Autocomplete setup complete
```

**When you type:**
```
📝 Input detected in #origin: "par"
🔍 Search results for "par": 5 airports found
```

## Common Issues & Fixes

### Issue 1: No dropdown appears
**Symptoms:** You type but nothing shows up

**Check:**
1. Open Console (F12) - any errors?
2. Type at least 2 characters
3. Check if AIRPORTS is loaded: In console type: `Object.keys(AIRPORTS).length`
   - Should return a number > 0
   - If 0 or undefined, AIRPORTS not loaded

**Fix:**
- Make sure `app.py` passes `AIRPORTS` to template
- Check `base.html` has the script loading AIRPORTS
- Refresh page (Ctrl+F5 for hard refresh)

### Issue 2: "AIRPORTS is not defined"
**Symptoms:** Console shows error about AIRPORTS

**Fix:**
```python
# In app.py, make sure home() route has:
return render_template('home.html', AIRPORTS=AIRPORTS)
```

### Issue 3: Dropdown appears but empty
**Symptoms:** You see the dropdown box but no results

**Check Console for:**
```
🔍 Search results for "xxx": 0 airports found
```

**Possible causes:**
- Airports data is empty
- Search logic not working
- Type: `AIRPORTS` in console to see the data

### Issue 4: JavaScript not loading
**Symptoms:** No console messages at all

**Check:**
1. View page source (Right-click → View Page Source)
2. Look for: `<script src="/static/js/script.js"></script>`
3. Click the link - does it load?
4. Check browser console for 404 errors

**Fix:**
- Make sure `script.js` is in `static/js/` folder
- Clear browser cache (Ctrl+Shift+Del)
- Hard refresh (Ctrl+F5)

## Manual Testing Steps

### Step 1: Verify AIRPORTS is loaded
Open Console (F12) and type:
```javascript
AIRPORTS
```
Should show an object with airport codes

### Step 2: Check if autocomplete function exists
In console type:
```javascript
document.getElementById('origin')
```
Should return the input element (not null)

### Step 3: Manually trigger autocomplete
```javascript
const input = document.getElementById('origin');
input.value = 'paris';
input.dispatchEvent(new Event('input'));
```
Dropdown should appear

### Step 4: Check airportsList
In console after page loads:
```javascript
// This won't work in console but check the init message
// Should see: "🔍 Airport Autocomplete initialized with X airports"
```

## Debug Mode - Add This to Your Page

Add this script to `home.html` temporarily to test:

```html
<script>
window.addEventListener('load', function() {
    console.log('=== AUTOCOMPLETE DEBUG ===');
    console.log('AIRPORTS loaded:', typeof AIRPORTS !== 'undefined');
    console.log('Number of airports:', Object.keys(AIRPORTS || {}).length);
    console.log('Origin input exists:', !!document.getElementById('origin'));
    console.log('Destination input exists:', !!document.getElementById('destination'));
    console.log('script.js loaded:', typeof setupAirportAutocomplete);
    
    // Test search manually
    setTimeout(() => {
        const origin = document.getElementById('origin');
        if (origin) {
            origin.value = 'par';
            origin.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('Manual test triggered for "par"');
        }
    }, 1000);
});
</script>
```

## What Should Happen

### When you type "paris":
1. Console: `📝 Input detected in #origin: "paris"`
2. Console: `🔍 Search results for "paris": X airports found`
3. Dropdown appears below input
4. You see: **CDG - Paris, FR** (and similar)

### When you click a result:
1. Input field shows the IATA code (e.g., "CDG")
2. Dropdown disappears
3. Ready to search flights

## Still Not Working?

### Last Resort Checks:

1. **Check file paths:**
   ```
   templates/base.html exists?
   templates/home.html exists?
   static/js/script.js exists?
   ```

2. **Browser compatibility:**
   - Try Chrome, Firefox, or Edge
   - Disable browser extensions
   - Try Incognito/Private mode

3. **Flask server running?**
   ```
   python app.py
   # Should show: Running on http://127.0.0.1:5000
   ```

4. **Check for conflicting JavaScript:**
   - Any other autocomplete libraries?
   - jQuery autocomplete?
   - Check for JavaScript errors in console

## Get Detailed Logs

Add this at the TOP of `script.js` (line 1):
```javascript
console.log('🚀 script.js is loading...');
```

Add this at the BOTTOM of `script.js`:
```javascript
console.log('✅ script.js finished loading');
```

You should see both messages when page loads.

## Contact Info

If still not working, check:
1. Browser console screenshot
2. Network tab (F12 → Network) - any red errors?
3. AIRPORTS value in console
4. Does simple_test.html work?

This will help diagnose the issue!
