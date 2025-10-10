# HaleWay - Style Guide & UI Patterns

**Last Updated**: 2025-10-09
**Framework**: Custom CSS (No Bootstrap/Tailwind)
**Approach**: Mobile-First, BEM Methodology

## Theme Configuration

### Brand Colors
- **Primary (Ocean Blue)**: `#2E86AB` - Trust, calm, travel-friendly
- **Secondary (Sunset Coral)**: `#FF6B6B` - Warm, energetic, fun
- **Tertiary (Sandy Beige)**: `#F4E8C1` - Neutral, easy on eyes
- **Accent (Palm Green)**: `#06A77D` - Fresh, adventurous

### Neutrals
- **Dark Text**: `#2C3E50`
- **Light Background**: `#F8F9FA`
- **Borders/Dividers**: `#E0E0E0`

### Design System
- **Border Radius**: 8px (friendly, modern)
- **Shadow Style**: Medium shadows (clear depth)
- **Font**: System fonts (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`)

## CSS Architecture

### File Structure
```
static/css/
├── base.css                 # CSS variables, typography, utilities
├── components/
│   ├── buttons.css         # Button variants and states
│   ├── forms.css           # Form controls and layouts
│   ├── cards.css           # Card components
│   ├── modals.css          # Modal dialogs
│   ├── tables.css          # Data table styles
│   ├── breadcrumbs.css     # Breadcrumb navigation
│   └── navigation.css      # Navigation components
└── apps/
    ├── trips.css           # Trip-specific styles
    ├── packing.css         # Packing list styles
    ├── grocery.css         # Grocery list styles
    └── ...                 # Other app-specific styles
```

### CSS Variables (base.css)
```css
:root {
    /* Brand Colors */
    --primary-color: #2E86AB;
    --secondary-color: #FF6B6B;
    --accent-color: #06A77D;
    --beige: #F4E8C1;

    /* Neutrals */
    --text-primary: #2C3E50;
    --text-secondary: #6c757d;
    --bg-primary: #FFFFFF;
    --bg-secondary: #F8F9FA;
    --border-color: #E0E0E0;

    /* Spacing (Updated 2025-10-09 for UI compression) */
    --spacing-xs: 4px;
    --spacing-sm: 6px;    /* Reduced from 8px */
    --spacing-md: 12px;   /* Reduced from 16px */
    --spacing-lg: 16px;   /* Reduced from 24px */
    --spacing-xl: 24px;   /* Reduced from 32px */
    --spacing-xxl: 40px;  /* Reduced from 48px */

    /* Border Radius */
    --border-radius-sm: 4px;
    --border-radius-md: 8px;
    --border-radius-lg: 12px;

    /* Shadows */
    --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.15);

    /* Component Sizing */
    --button-height: 44px;      /* Touch-friendly */
    --input-height: 44px;
    --touch-target: 44px;
}
```

### Responsive Breakpoints
```css
/* Mobile-first approach */
/* Default: Mobile (< 576px) */

@media (min-width: 576px) {
    /* Small tablets */
}

@media (min-width: 768px) {
    /* Tablets */
}

@media (min-width: 992px) {
    /* Desktops */
}

@media (min-width: 1200px) {
    /* Large desktops */
}
```

## Component Patterns

### Buttons

**Primary Button**:
```html
<button class="btn btn-primary">Primary Action</button>
```

**Secondary Button**:
```html
<button class="btn btn-outline">Secondary Action</button>
```

**Danger Button**:
```html
<button class="btn btn-danger">Delete</button>
```

**CSS**:
```css
.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.5;
    text-align: center;
    border: 1px solid transparent;
    border-radius: var(--border-radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary {
    background-color: var(--primary-color);
    color: #fff;
}

.btn-primary:hover {
    background-color: #246a8a;
    transform: translateY(-2px);
}

.btn-outline {
    background-color: transparent;
    color: var(--primary-color);
    border: 2px solid var(--primary-color);
}

.btn-outline:hover {
    background-color: var(--primary-color);
    color: #fff;
}
```

### Forms

**Modern Form Pattern** (Established 2025-10-09):
All item forms (packing, grocery, etc.) use this consistent styling.

#### Template Structure
```html
{% extends "base.html" %}

{% block extra_css %}
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<style>
    /* Modern form styling */
    .add-item-container {
        max-width: 700px;
        margin: 0 auto;
        padding: var(--spacing-md);
    }

    .page-header {
        text-align: center;
        margin-bottom: var(--spacing-xl);
    }

    .page-icon {
        font-size: 3rem;
        display: block;
        margin-bottom: var(--spacing-sm);
    }

    .modern-form-card {
        background: white;
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-xl);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05),
                    0 10px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(46, 134, 171, 0.1);
    }

    .quick-tips {
        background: linear-gradient(135deg, #E8F4F8 0%, #F0F8FB 100%);
        border-left: 4px solid var(--primary-color);
        border-radius: var(--border-radius-md);
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-xl);
    }

    .quick-tips h3 {
        color: var(--primary-color);
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: var(--spacing-md);
    }

    .quick-tips ul {
        list-style: none;
        padding-left: 0;
    }

    .quick-tips li:before {
        content: "→";
        color: var(--accent-color);
        font-weight: bold;
        margin-right: var(--spacing-sm);
    }

    .form-control {
        width: 100%;
        padding: 0.75rem;
        font-size: 1rem;
        border: 2px solid #ddd;
        border-radius: var(--border-radius-md);
        transition: all 0.2s ease;
    }

    .form-control:hover {
        border-color: rgba(46, 134, 171, 0.4);
    }

    .form-control:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 4px rgba(46, 134, 171, 0.15);
        transform: translateY(-1px);
    }

    .form-actions {
        display: flex;
        gap: var(--spacing-md);
        margin-top: var(--spacing-xl);
    }

    @media (max-width: 576px) {
        .form-actions {
            flex-direction: column;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="add-item-container">
    <div class="page-header">
        <nav class="breadcrumb">
            <!-- Breadcrumb navigation -->
        </nav>
        <span class="page-icon">🎒</span>
        <h1>Form Title</h1>
        <p class="page-subtitle">Description of what this form does</p>
    </div>

    <div class="modern-form-card">
        <div class="quick-tips">
            <h3>💡 Quick Tips</h3>
            <ul>
                <li>Helpful tip 1</li>
                <li>Helpful tip 2</li>
            </ul>
        </div>

        <form method="post">
            {% csrf_token %}
            <!-- Form fields here -->

            <div class="form-actions">
                <a href="..." class="btn btn-outline">Cancel</a>
                <button type="submit" class="btn btn-primary">✓ Submit</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script>
    $(document).ready(function() {
        $('.category-select').select2({
            tags: true,
            placeholder: 'Select or type a category...',
            allowClear: false,
            width: '100%',
            createTag: function (params) {
                var term = $.trim(params.term);
                if (term === '') return null;
                return {
                    id: term,
                    text: term + ' (create new)',
                    newTag: true
                }
            },
            templateResult: function(data) {
                if (data.newTag) {
                    return $('<span style="color: var(--accent-color); font-weight: 600;">+ ' + data.text + '</span>');
                }
                return data.text;
            }
        });

        // Auto-focus on primary field
        $('#id_item_name').focus();
    });
</script>
{% endblock %}
```

#### Key Features
- **Select2 Category Dropdown**: Searchable, create-new capability
- **Modern Card Design**: Gradient shadows, rounded corners
- **Quick Tips Box**: Contextual help with arrow bullets
- **Breadcrumb Navigation**: Clear page hierarchy
- **Auto-focus**: Primary field focused on load
- **Responsive**: Mobile-optimized layout

#### When to Use
- Item creation/editing forms (packing, grocery, budget)
- Bulk add forms
- Any form with category selection
- Settings/configuration forms

#### Reference Examples
- `/apps/grocery/templates/grocery/item_form.html`
- `/apps/packing/templates/packing/bulk_add_items.html`

### Cards

**Standard Card**:
```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Card Title</h3>
    </div>
    <div class="card-body">
        <p>Card content here</p>
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Action</button>
    </div>
</div>
```

**CSS**:
```css
.card {
    background: white;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-md);
    overflow: hidden;
    transition: transform 0.2s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.card-header {
    padding: var(--spacing-lg);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
}

.card-body {
    padding: var(--spacing-lg);
}

.card-footer {
    padding: var(--spacing-lg);
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
}
```

### Modals

**Modal Structure**:
```html
<div id="myModal" class="modal">
    <div class="modal-overlay"></div>
    <div class="modal-content">
        <div class="modal-header">
            <h2 class="modal-title">Modal Title</h2>
            <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Modal content -->
        </div>
        <div class="modal-footer">
            <button class="btn btn-outline">Cancel</button>
            <button class="btn btn-primary">Confirm</button>
        </div>
    </div>
</div>
```

**CSS** (`components/modals.css`):
```css
.modal {
    display: none;  /* Hidden by default */
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 9999;
}

.modal.active {
    display: flex;
    justify-content: center;
    align-items: center;
}

.modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
}

.modal-content {
    position: relative;
    background: white;
    border-radius: var(--border-radius-lg);
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: var(--shadow-lg);
    z-index: 10000;
}

.modal-header {
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-close {
    background: none;
    border: none;
    font-size: 2rem;
    cursor: pointer;
    color: var(--text-secondary);
}

.modal-close:hover {
    color: var(--text-primary);
}
```

**JavaScript**:
```javascript
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal when clicking overlay
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', () => {
        overlay.closest('.modal').classList.remove('active');
    });
});
```

### Breadcrumbs

**HTML**:
```html
<nav class="breadcrumb">
    <a href="/" class="breadcrumb-item">Dashboard</a>
    <span class="breadcrumb-separator">›</span>
    <a href="/trips/" class="breadcrumb-item">Trips</a>
    <span class="breadcrumb-separator">›</span>
    <span class="breadcrumb-item active">Trip Detail</span>
</nav>
```

**CSS** (`components/breadcrumbs.css`):
```css
.breadcrumb {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) 0;
    font-size: 0.9rem;
}

.breadcrumb-item {
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.2s ease;
}

.breadcrumb-item:hover {
    color: var(--primary-color);
}

.breadcrumb-item.active {
    color: var(--text-primary);
    font-weight: 500;
}

.breadcrumb-separator {
    color: var(--border-color);
}
```

### Collapsible Sections

**HTML**:
```html
<div class="section-card" data-section="activities">
    <div class="section-header" onclick="toggleSection('activities')">
        <h2 class="section-title">
            <span class="section-icon">🎯</span>
            Activities
            <span class="item-count">5</span>
        </h2>
        <button class="collapse-toggle">−</button>
    </div>
    <div class="section-content">
        <!-- Section content -->
    </div>
</div>
```

**JavaScript**:
```javascript
function toggleSection(sectionName) {
    const section = document.querySelector(`[data-section="${sectionName}"]`);
    const content = section.querySelector('.section-content');
    const toggle = section.querySelector('.collapse-toggle');

    section.classList.toggle('collapsed');

    // Save preference to localStorage
    const tripId = document.querySelector('[data-trip-id]').dataset.tripId;
    const collapsed = JSON.parse(localStorage.getItem(`trip_${tripId}_collapsed`) || '{}');
    collapsed[sectionName] = section.classList.contains('collapsed');
    localStorage.setItem(`trip_${tripId}_collapsed`, JSON.stringify(collapsed));
}

// Restore collapsed state on page load
document.addEventListener('DOMContentLoaded', () => {
    const tripId = document.querySelector('[data-trip-id]')?.dataset.tripId;
    if (!tripId) return;

    const collapsed = JSON.parse(localStorage.getItem(`trip_${tripId}_collapsed`) || '{}');
    Object.entries(collapsed).forEach(([sectionName, isCollapsed]) => {
        if (isCollapsed) {
            const section = document.querySelector(`[data-section="${sectionName}"]`);
            section?.classList.add('collapsed');
        }
    });
});
```

**CSS**:
```css
.section-card {
    background: white;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-md);
    margin-bottom: var(--spacing-lg);
    overflow: hidden;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    background: var(--bg-secondary);
    cursor: pointer;
    transition: background 0.2s ease;
}

.section-header:hover {
    background: #e9ecef;
}

.section-content {
    padding: var(--spacing-lg);
    max-height: 10000px;
    overflow: hidden;
    transition: max-height 0.3s ease, padding 0.3s ease;
}

.section-card.collapsed .section-content {
    max-height: 0;
    padding: 0 var(--spacing-lg);
}

.collapse-toggle {
    background: var(--primary-color);
    color: white;
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    transition: transform 0.3s ease;
}

.section-card.collapsed .collapse-toggle {
    transform: rotate(180deg);
}
```

## Design Patterns

### Checkbox with Strikethrough (Packing/Grocery Lists)

**HTML**:
```html
<div class="item-row" data-item-id="123">
    <input type="checkbox" class="item-checkbox" onchange="toggleItem(this, '123')">
    <span class="item-name">Item Name</span>
    <span class="item-quantity">2 lbs</span>
</div>
```

**CSS**:
```css
.item-row {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
    transition: background 0.2s ease;
}

.item-row:hover {
    background: var(--bg-secondary);
}

.item-checkbox {
    width: 24px;
    height: 24px;
    cursor: pointer;
}

.item-name {
    flex: 1;
    transition: all 0.2s ease;
}

.item-row.checked .item-name {
    text-decoration: line-through;
    color: var(--text-secondary);
    opacity: 0.6;
}
```

**JavaScript (AJAX Toggle)**:
```javascript
function toggleItem(checkbox, itemId) {
    const row = checkbox.closest('.item-row');
    const isChecked = checkbox.checked;

    // Optimistic UI update
    row.classList.toggle('checked', isChecked);

    // AJAX request
    fetch(`/grocery/item/${itemId}/toggle/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ is_purchased: isChecked })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            // Revert on error
            checkbox.checked = !isChecked;
            row.classList.toggle('checked', !isChecked);
        }
        // Update progress bar
        updateProgressBar(data.purchased_count, data.total_count);
    })
    .catch(error => {
        console.error('Error:', error);
        checkbox.checked = !isChecked;
        row.classList.toggle('checked', !isChecked);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### Progress Bars

**HTML**:
```html
<div class="progress-container">
    <div class="progress-label">
        <span>Progress</span>
        <span class="progress-text">15/30 items (50%)</span>
    </div>
    <div class="progress-bar-container">
        <div class="progress-bar" style="width: 50%"></div>
    </div>
</div>
```

**CSS**:
```css
.progress-container {
    margin-bottom: var(--spacing-lg);
}

.progress-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: var(--spacing-sm);
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.progress-bar-container {
    height: 10px;
    background: var(--bg-secondary);
    border-radius: var(--border-radius-sm);
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-color), var(--primary-color));
    transition: width 0.3s ease;
}
```

### Status Badges

**HTML**:
```html
<span class="badge badge-planning">Planning</span>
<span class="badge badge-active">Active</span>
<span class="badge badge-completed">Completed</span>
<span class="badge badge-dream">Dream Trip</span>
```

**CSS**:
```css
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    font-size: 0.85rem;
    font-weight: 500;
    border-radius: var(--border-radius-md);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-planning {
    background: #FFF3CD;
    color: #856404;
}

.badge-active {
    background: #D4EDDA;
    color: #155724;
}

.badge-completed {
    background: #CCE5FF;
    color: #004085;
}

.badge-dream {
    background: #F8D7DA;
    color: #721C24;
}
```

## Naming Conventions

### BEM Methodology
```css
/* Block */
.card { }

/* Element */
.card__header { }
.card__body { }
.card__footer { }

/* Modifier */
.card--highlighted { }
.card__header--dark { }
```

### Utility Classes
```css
/* Spacing */
.mt-1 { margin-top: var(--spacing-sm); }
.mt-2 { margin-top: var(--spacing-md); }
.mt-3 { margin-top: var(--spacing-lg); }

.mb-1 { margin-bottom: var(--spacing-sm); }
.mb-2 { margin-bottom: var(--spacing-md); }
.mb-3 { margin-bottom: var(--spacing-lg); }

/* Text */
.text-center { text-align: center; }
.text-muted { color: var(--text-secondary); }
.text-bold { font-weight: 600; }

/* Display */
.d-none { display: none; }
.d-block { display: block; }
.d-flex { display: flex; }
```

## Mobile-First Best Practices

### Always Start Mobile
```css
/* ✅ Good - Mobile first */
.hero {
    padding: 1rem;
    font-size: 1.5rem;
}

@media (min-width: 768px) {
    .hero {
        padding: 2rem;
        font-size: 2.5rem;
    }
}

/* ❌ Avoid - Desktop first */
.hero {
    padding: 2rem;
    font-size: 2.5rem;
}

@media (max-width: 767px) {
    .hero {
        padding: 1rem;
        font-size: 1.5rem;
    }
}
```

### Touch Targets
All interactive elements should be at least 44x44px for touch-friendliness:
```css
button, a.btn, .checkbox {
    min-width: 44px;
    min-height: 44px;
}
```

### Responsive Typography
```css
html {
    font-size: 16px;  /* Base font size */
}

@media (min-width: 768px) {
    html {
        font-size: 18px;  /* Larger on tablets+ */
    }
}

h1 { font-size: 2rem; }  /* Scales with base font */
h2 { font-size: 1.5rem; }
h3 { font-size: 1.25rem; }
```

## Performance Considerations

### Minimize CSS
- Use CSS variables for theming
- Avoid deep nesting (max 3 levels)
- Reuse components across pages

### Lazy Load Images
```html
<img src="placeholder.jpg" data-src="actual-image.jpg" loading="lazy" alt="...">
```

### Critical CSS
- Inline critical above-the-fold CSS in `<head>`
- Load component CSS asynchronously

## Accessibility

### Color Contrast
All text must meet WCAG 2.1 AA standards:
- Normal text: 4.5:1 contrast ratio
- Large text (18pt+): 3:1 contrast ratio

### Focus States
```css
*:focus {
    outline: 3px solid var(--primary-color);
    outline-offset: 2px;
}

button:focus {
    box-shadow: 0 0 0 4px rgba(46, 134, 171, 0.25);
}
```

### Screen Reader Support
```html
<!-- Use semantic HTML -->
<nav aria-label="Main navigation">
    <ul>
        <li><a href="/">Home</a></li>
    </ul>
</nav>

<!-- Provide alt text -->
<img src="photo.jpg" alt="Beach sunset in Maui">

<!-- Use ARIA when needed -->
<button aria-label="Close modal" aria-pressed="false">×</button>
```

---

**Summary**: HaleWay uses a custom CSS system built for speed, maintainability, and mobile-first responsive design. All components follow BEM naming, use CSS variables for theming, and prioritize accessibility. For technical architecture, see `docs/ARCHITECTURE.md`. For quick reference, see `CLAUDE.md`.
