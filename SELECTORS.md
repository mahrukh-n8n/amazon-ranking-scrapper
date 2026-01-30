# Amazon Selectors Configuration
#
# This file documents the CSS selectors used to interact with Amazon's website.
# Amazon frequently changes their HTML structure, so these may need updating.
#
# HOW TO UPDATE SELECTORS:
# 1. Open the Amazon page in Chrome/Edge
# 2. Right-click on the element you need to interact with
# 3. Click "Inspect" to open Developer Tools
# 4. Find the element's CSS selector (class, id, or data-attribute)
# 5. Update the corresponding selector in the source code
# 6. Test the change
#
# Last Updated: 2026-01-30

# =============================================================================
# LOCATION HANDLER SELECTORS (src/location_handler.py)
# =============================================================================

# Delivery location display (shows current zip/city)
LOCATION_DISPLAY = "#glow-ingress-line2"

# Click to open location modal
LOCATION_BUTTON = "#nav-global-location-popover-link"

# Zip code input field in modal
ZIP_INPUT = "#GLUXZipUpdateInput"

# Apply/Update button after entering zip
ZIP_APPLY = "#GLUXZipUpdate"

# Error message when zip is invalid
ZIP_ERROR = "#GLUXZipError"

# Change link (when location already set)
CHANGE_LINK_SELECTORS = [
    "#GLUXChangePostalCodeLink",
    "a[data-action='GLUXPostalUpdateAction']",
    "#GLUXZipInputSection a.a-link-normal",
]

# Confirm/Done button to close modal
CONFIRM_SELECTORS = [
    "#GLUXConfirmClose",
    "button[name='glowDoneButton']",
    ".a-popover-footer button.a-button-primary",
    "input[data-action='GLUXConfirmAction']",
]

# Modal container (to detect if modal is still open)
MODAL_CONTAINER = ".a-modal-scroller"

# =============================================================================
# SEARCH SELECTORS (src/scraper.py)
# =============================================================================

# Search input box
SEARCH_BOX = "#twotabsearchtextbox"

# Search submit button (fallback if Enter key fails)
SEARCH_BUTTON = "#nav-search-submit-button"

# Individual search result container
SEARCH_RESULT = 'div[data-component-type="s-search-result"]'

# =============================================================================
# SPONSORED DETECTION SELECTORS (src/scraper.py)
# =============================================================================

# Sponsored label CSS selectors
SPONSORED_LABEL_SELECTORS = [
    ".puis-sponsored-label-text",
    ".s-sponsored-label-info-icon",
    "[data-component-type='sp-sponsored-result']",
    ".s-label-popover-default[aria-label*='ponsored']",
]

# Data attributes that indicate sponsored
SPONSORED_DATA_ATTRS = [
    "data-asin-ad-id",
    "data-ad-type",
]

# Text indicators (multilingual)
SPONSORED_TEXT = [
    "Sponsored",      # English
    "Gesponsert",     # German
    "Sponsorisé",     # French
    "Patrocinado",    # Spanish
    "Sponsorizzato",  # Italian
]

# =============================================================================
# CAPTCHA DETECTION SELECTORS (src/location_handler.py)
# =============================================================================

# Captcha input field
CAPTCHA_INPUT = "input#captchacharacters"

# Page titles that indicate captcha
CAPTCHA_TITLES = [
    "Robot Check",
    "Something went wrong",
]

# =============================================================================
# HOW TO FIND NEW SELECTORS
# =============================================================================
#
# 1. USING BROWSER DEVELOPER TOOLS:
#    - Open Chrome/Edge
#    - Navigate to Amazon
#    - Press F12 to open Developer Tools
#    - Click the "Select element" tool (arrow icon, or Ctrl+Shift+C)
#    - Click on the element you need
#    - In the Elements panel, right-click the highlighted HTML
#    - Choose "Copy" > "Copy selector" for a CSS selector
#
# 2. FINDING STABLE SELECTORS:
#    - Prefer IDs (#element-id) - most stable
#    - Use data attributes ([data-component-type="..."]) - fairly stable
#    - Avoid deeply nested class selectors - break easily
#    - Avoid auto-generated class names (random strings)
#
# 3. TESTING SELECTORS:
#    - In Developer Tools Console, type:
#      document.querySelector('YOUR_SELECTOR')
#    - If it returns the element, the selector works
#    - If it returns null, the selector is wrong
#
# 4. COMMON AMAZON PATTERNS:
#    - IDs often start with: nav-, glow-, twotab-, GLUX
#    - Data attributes: data-component-type, data-asin, data-action
#    - Classes: a-button, a-section, s-result-item
#
# =============================================================================
