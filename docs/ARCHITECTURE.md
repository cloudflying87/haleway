# HaleWay - Technical Architecture

**Last Updated**: 2025-10-09
**Django Version**: 5.0+
**Database**: PostgreSQL 15+

## Table of Contents
1. [Database Schema](#database-schema)
2. [Model Relationships](#model-relationships)
3. [Database Indexes](#database-indexes)
4. [Permission System](#permission-system)
5. [API Endpoints](#api-endpoints)
6. [Email System](#email-system)
7. [Integrations](#integrations)

---

## Database Schema

### User & Family Management

#### User (accounts.User)
- Custom Django user model
- Email-based authentication
- Fields: email, first_name, last_name, date_joined

#### Family (families.Family)
- **id**: UUID (PK)
- **name**: CharField(200) - Family display name
- **created_at**: DateTimeField
- **updated_at**: DateTimeField
- **Methods**: `get_owner()`, `get_admins()`, `get_all_members()`
- **Business Rules**: Must have exactly one owner

#### FamilyMember (families.FamilyMember)
- **id**: UUID (PK)
- **family**: FK → Family
- **user**: FK → User
- **role**: CharField - choices: `owner`, `admin`, `member`
- **joined_at**: DateTimeField
- **Unique Constraint**: (family, user)
- **Indexes**: (family, role)
- **Methods**: `is_owner()`, `is_admin()`, `can_manage_members()`

#### FamilyInvitation (families.FamilyInvitation)
- **id**: UUID (PK)
- **family**: FK → Family
- **email**: EmailField
- **token**: CharField(64) - unique
- **invited_by**: FK → User
- **status**: CharField - choices: `pending`, `accepted`, `expired`
- **created_at**: DateTimeField
- **expires_at**: DateTimeField (auto-set to 7 days)
- **Indexes**: (family, status), (email, status), (token)
- **Methods**: `is_valid()`, `mark_accepted()`, `mark_expired()`

---

### Trip Core

#### Trip (trips.Trip)
- **id**: UUID (PK)
- **family**: FK → Family
- **name**: CharField(200) - e.g., "Hawaii 2025"
- **destination_name**: CharField(200) - e.g., "Maui"
- **start_date**: DateField (nullable for dream trips)
- **end_date**: DateField (nullable for dream trips)
- **status**: CharField - choices: `dream`, `planning`, `active`, `completed`
- **created_by**: FK → User
- **created_at**: DateTimeField
- **updated_at**: DateTimeField
- **Indexes**: (family, status), (start_date)
- **Methods**: `duration_days()`, `is_upcoming()`, `is_active()`, `is_past()`

#### Resort (trips.Resort)
- **id**: UUID (PK)
- **trip**: OneToOneField → Trip
- **name**: CharField(200)
- **website_url**: URLField
- **phone_number**: CharField(20)
- **check_in_time**: TimeField (nullable)
- **check_out_time**: TimeField (nullable)
- **Address Fields**: address_line1, address_line2, city, state, zip_code, country
- **latitude**: DecimalField(9,6) (nullable)
- **longitude**: DecimalField(9,6) (nullable)
- **general_notes**: TextField
- **Methods**: `get_full_address()`

#### TripResortOption (trips.TripResortOption)
*For dream trips with multiple resort possibilities*
- **id**: UUID (PK)
- **trip**: FK → Trip (for dream trips only)
- **name**: CharField(200)
- **website_url**: URLField
- **phone_number**: CharField(20)
- **Address Fields**: Same as Resort
- **latitude/longitude**: DecimalField(9,6)
- **estimated_cost_per_night**: DecimalField(10,2)
- **pros**: TextField - what's good about this resort
- **cons**: TextField - concerns or drawbacks
- **rating**: IntegerField(1-5) - preliminary rating
- **is_preferred**: BooleanField - mark favorite option
- **order**: IntegerField - for ranking
- **general_notes**: TextField
- **created_at/updated_at**: DateTimeField
- **Indexes**: (trip, order), (trip, is_preferred)
- **Ordering**: order, -is_preferred, name

#### ResortWishlist (trips.ResortWishlist)
*Family-level wishlist of resorts for future trips*
- **id**: UUID (PK)
- **family**: FK → Family
- **name**: CharField(200)
- **destination**: CharField(200) - e.g., "Maui", "Paris"
- **website_url**: URLField
- **Address Fields**: Same as Resort
- **latitude/longitude**: DecimalField(9,6)
- **description**: TextField - why we want to visit
- **estimated_cost_per_night**: DecimalField(10,2)
- **tags**: CharField(500) - comma-separated
- **notes**: TextField - research notes
- **added_by**: FK → User
- **is_favorite**: BooleanField
- **visited**: BooleanField
- **visited_trip**: FK → Trip (nullable)
- **created_at/updated_at**: DateTimeField
- **Indexes**: (family, is_favorite), (family, visited), (family, destination)
- **Ordering**: -is_favorite, destination, name
- **Methods**: `get_full_address()`, `get_tags_list()`

---

### Notes System

#### NoteCategory (notes.NoteCategory)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **name**: CharField(100)
- **color_code**: CharField(7) - hex color
- **order**: IntegerField
- **Unique Constraint**: (trip, name)
- **Indexes**: (trip, order)

#### Note (notes.Note)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **category**: FK → NoteCategory (nullable)
- **title**: CharField(200)
- **content**: TextField
- **is_pinned**: BooleanField
- **search_vector**: SearchVectorField (PostgreSQL full-text search)
- **created_by**: FK → User
- **created_at**: DateTimeField
- **updated_at**: DateTimeField
- **Indexes**: (trip, category), (trip, is_pinned), GIN index on search_vector
- **Ordering**: -is_pinned, -updated_at

---

### Activities & Itinerary

#### Activity (activities.Activity)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **name**: CharField(200)
- **description**: TextField
- **website_url**: URLField
- **Address Fields**: address_line1, address_line2, city, state, zip_code
- **latitude**: DecimalField(9,6)
- **longitude**: DecimalField(9,6)
- **distance_from_resort**: DecimalField(5,2) - miles
- **travel_time_from_resort**: IntegerField - minutes
- **estimated_cost**: DecimalField(10,2)
- **estimated_duration**: IntegerField - minutes
- **Pre-trip Fields**:
  - **pre_trip_priority**: IntegerField (0 = unranked, lower = higher priority)
- **Post-trip Fields**:
  - **post_trip_rating**: IntegerField(1-5) (nullable)
  - **post_trip_notes**: TextField (nullable)
  - **is_favorite**: BooleanField - "would do again"
- **created_by**: FK → User
- **created_at/updated_at**: DateTimeField
- **Indexes**: (trip, pre_trip_priority), (trip, post_trip_rating), (trip, is_favorite)
- **Methods**: `has_rating()`, `get_duration_display()`, `get_full_address()`

#### DailyItinerary (itinerary.DailyItinerary)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **activity**: FK → Activity (nullable - can be general event)
- **date**: DateField
- **time_start**: TimeField (nullable)
- **time_end**: TimeField (nullable)
- **title**: CharField(200) - for non-activity events
- **notes**: TextField (nullable)
- **order**: IntegerField - for sorting multiple items on same day
- **Indexes**: (trip, date), (trip, date, order)
- **Ordering**: date, time_start, order

---

### Packing & Grocery Lists

#### PackingListTemplate (packing.PackingListTemplate)
- **id**: UUID (PK)
- **name**: CharField(200)
- **description**: TextField
- **is_system_template**: BooleanField (prevents deletion)
- **created_by**: FK → User (nullable for system templates)
- **created_at/updated_at**: DateTimeField
- **Methods**: `duplicate_for_trip(trip, assigned_to, list_name)`

#### PackingListTemplateItem (packing.PackingListTemplateItem)
- **id**: UUID (PK)
- **template**: FK → PackingListTemplate
- **category**: CharField(100)
- **item_name**: CharField(200)
- **quantity**: IntegerField
- **notes**: TextField
- **order**: IntegerField
- **Indexes**: (template, category)
- **Ordering**: category, order, item_name

#### TripPackingList (packing.TripPackingList)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **name**: CharField(200)
- **based_on_template**: FK → PackingListTemplate (nullable)
- **assigned_to**: FK → User (nullable)
- **Indexes**: (trip), (assigned_to)
- **Methods**: `get_packed_percentage()`, `get_packed_count()`, `get_total_count()`, `save_as_template()`

#### TripPackingItem (packing.TripPackingItem)
- **id**: UUID (PK)
- **packing_list**: FK → TripPackingList
- **category**: CharField(100)
- **item_name**: CharField(200)
- **quantity**: IntegerField
- **notes**: TextField
- **is_packed**: BooleanField
- **order**: IntegerField
- **Indexes**: (packing_list, category), (packing_list, is_packed)
- **Ordering**: category, order, item_name

#### GroceryListTemplate (grocery.GroceryListTemplate)
- **id**: UUID (PK)
- **family**: FK → Family (nullable for system templates)
- **name**: CharField(200)
- **description**: TextField
- **is_system_template**: BooleanField
- **created_by**: FK → User (nullable)
- **created_at/updated_at**: DateTimeField
- **Indexes**: (family, is_system_template)
- **Methods**: `duplicate_for_trip(trip, assigned_to, list_name)`

#### GroceryListTemplateItem (grocery.GroceryListTemplateItem)
- **id**: UUID (PK)
- **template**: FK → GroceryListTemplate
- **category**: CharField(100) - Produce, Snacks, Beverages, etc.
- **item_name**: CharField(200)
- **quantity**: CharField(100) - e.g., "2 lbs", "1 gallon"
- **notes**: TextField
- **order**: IntegerField
- **Indexes**: (template, category)
- **Ordering**: category, order, item_name

#### TripGroceryList (grocery.TripGroceryList)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **name**: CharField(200)
- **based_on_template**: FK → GroceryListTemplate (nullable)
- **assigned_to**: FK → User (nullable)
- **shopping_date**: DateField (nullable)
- **store_name**: CharField(200)
- **created_at/updated_at**: DateTimeField
- **Indexes**: (trip), (assigned_to)
- **Methods**: `get_purchased_percentage()`, `get_purchased_count()`, `get_total_count()`, `save_as_template()`

#### TripGroceryItem (grocery.TripGroceryItem)
- **id**: UUID (PK)
- **grocery_list**: FK → TripGroceryList
- **category**: CharField(100)
- **item_name**: CharField(200)
- **quantity**: CharField(100)
- **notes**: TextField
- **is_purchased**: BooleanField
- **order**: IntegerField
- **created_at/updated_at**: DateTimeField
- **Indexes**: (grocery_list, category), (grocery_list, is_purchased)
- **Ordering**: category, order, item_name

---

### Budget Tracking

#### BudgetCategory (budget.BudgetCategory)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **name**: CharField(100)
- **color_code**: CharField(7) - hex color (8 color choices)
- **order**: IntegerField
- **Unique Constraint**: (trip, name)
- **Indexes**: (trip, order)
- **Methods**: `get_total_estimated()`, `get_total_actual()`

#### BudgetItem (budget.BudgetItem)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **category**: FK → BudgetCategory (nullable)
- **description**: CharField(200)
- **estimated_amount**: DecimalField(10,2)
- **actual_amount**: DecimalField(10,2) (nullable)
- **paid_by**: FK → User (nullable)
- **payment_date**: DateField (nullable)
- **notes**: TextField
- **created_at/updated_at**: DateTimeField
- **Indexes**: (trip, category), (trip, paid_by), (payment_date)
- **Ordering**: category__order, category__name, created_at
- **Properties**: `is_paid`, `variance`, `variance_percentage`

---

### Memories & Media

#### TripPhoto (memories.TripPhoto)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **activity**: FK → Activity (nullable)
- **daily_itinerary**: FK → DailyItinerary (nullable)
- **image**: ImageField (upload_to='trip_photos/%Y/%m/%d/')
- **caption**: TextField (nullable)
- **taken_date**: DateField (nullable)
- **uploaded_by**: FK → User
- **uploaded_at**: DateTimeField
- **Indexes**: (trip, taken_date), (trip, uploaded_at), (activity), (daily_itinerary)
- **Ordering**: -taken_date, -uploaded_at

#### DailyJournal (memories.DailyJournal)
- **id**: UUID (PK)
- **trip**: FK → Trip
- **date**: DateField
- **content**: TextField
- **weather**: CharField(100) (nullable) - e.g., "Sunny, 78°F"
- **mood_rating**: IntegerField(1-5) (nullable)
- **created_by**: FK → User
- **created_at/updated_at**: DateTimeField
- **Unique Constraint**: (trip, date, created_by)
- **Indexes**: (trip, date), (trip, created_by)
- **Ordering**: -date

---

## Model Relationships

### Core Relationships
```
Family (1) ←→ (N) FamilyMember (N) ←→ (1) User
Family (1) ←→ (N) FamilyInvitation
Family (1) ←→ (N) Trip
Family (1) ←→ (N) ResortWishlist
Trip (1) ←→ (1) Resort
Trip (1) ←→ (N) TripResortOption (for dream trips)
Trip (1) ←→ (N) NoteCategory ←→ (N) Note
Trip (1) ←→ (N) Activity
Trip (1) ←→ (N) DailyItinerary
Trip (1) ←→ (N) TripPackingList ←→ (N) TripPackingItem
Trip (1) ←→ (N) TripGroceryList ←→ (N) TripGroceryItem
Trip (1) ←→ (N) BudgetCategory ←→ (N) BudgetItem
Trip (1) ←→ (N) TripPhoto
Trip (1) ←→ (N) DailyJournal
PackingListTemplate (1) ←→ (N) PackingListTemplateItem
GroceryListTemplate (1) ←→ (N) GroceryListTemplateItem
```

### User-Created Content
- User creates Families (via FamilyMember with role=owner)
- User creates Trips (created_by FK)
- User creates Activities, Notes, Photos, Journals (created_by FK)
- User can be assigned Packing Lists and Grocery Lists

### Template System
- System templates: is_system_template=True, family=None
- Family templates: is_system_template=False, family=FK
- Templates can be duplicated to create trip-specific lists
- Trip lists can be saved as templates for reuse

---

## Database Indexes

### Critical Indexes for Performance

**Trip Queries**:
- `(family, status)` - Filter trips by family and status
- `(start_date)` - Sort trips chronologically

**Activity Queries**:
- `(trip, pre_trip_priority)` - Priority ordering
- `(trip, post_trip_rating)` - Filter highly-rated activities
- `(trip, is_favorite)` - Filter favorite activities

**Note Queries**:
- `(trip, category)` - Filter notes by category
- `(trip, is_pinned)` - Show pinned notes first
- GIN index on `search_vector` - Full-text search

**Itinerary Queries**:
- `(trip, date)` - Fetch items for specific day
- `(trip, date, order)` - Sort items within a day

**Packing/Grocery Queries**:
- `(packing_list, category)` / `(grocery_list, category)` - Group by category
- `(packing_list, is_packed)` / `(grocery_list, is_purchased)` - Filter completed items
- `(trip)` - Fetch all lists for a trip
- `(assigned_to)` - Fetch user's assigned lists

**Budget Queries**:
- `(trip, category)` - Group expenses by category
- `(trip, paid_by)` - Filter by payer
- `(payment_date)` - Sort by payment date

**Family Queries**:
- `(family, role)` - Find owners/admins
- `(family, status)` - Filter pending/accepted invitations
- `(email, status)` - Look up invitations by email
- `(token)` - Accept invitation by token

**Resort Wishlist**:
- `(family, is_favorite)` - Filter family favorites
- `(family, visited)` - Filter visited resorts
- `(family, destination)` - Search by location

**Resort Options (Dream Trips)**:
- `(trip, order)` - Rank resort options
- `(trip, is_preferred)` - Show preferred option

---

## Permission System

### Role-Based Access Control

**Owner** (one per family):
- All admin permissions
- Cannot be removed from family
- Can delete family
- Can transfer ownership

**Admin** (multiple per family):
- Invite/remove members (except owner)
- Delete categories, items, lists
- Edit all family trips
- Manage family settings

**Member** (standard):
- Create and edit own content (notes, activities, photos, journals)
- Edit trip details (not delete)
- Create packing/grocery lists
- Add budget items
- View all family content

### View-Level Permissions

**LoginRequiredMixin**: All views require authentication

**Permission Checks**:
- `get_queryset()`: Filter objects by family membership
- `form_valid()`: Validate user can modify object
- `delete()`: Check admin/owner role

**Example Pattern**:
```python
class TripUpdateView(LoginRequiredMixin, UpdateView):
    def get_queryset(self):
        # Only show trips user has access to via family
        return Trip.objects.filter(
            family__members__user=self.request.user
        ).select_related('family', 'resort')

    def form_valid(self, form):
        # Check if user is admin or trip creator
        trip = self.get_object()
        member = FamilyMember.objects.get(
            family=trip.family, user=self.request.user
        )
        if not (member.is_admin() or trip.created_by == self.request.user):
            messages.error(self.request, "Permission denied")
            return redirect('trips:trip_detail', pk=trip.pk)
        return super().form_valid(form)
```

---

## API Endpoints

### Internal AJAX Endpoints

**Trip Switching**:
- `GET /api/trips/` - List user's accessible trips (JSON)
- `POST /api/trips/set-current/` - Set current trip in session

**Checkbox Toggling**:
- `POST /packing/item/<id>/toggle/` - Toggle is_packed
- `POST /grocery/item/<id>/toggle/` - Toggle is_purchased

**Activity Ordering**:
- `POST /activities/<trip_id>/update-priority/` - Update pre_trip_priority via drag-and-drop

**All AJAX endpoints**:
- CSRF protection required
- LoginRequiredMixin
- JSON responses
- Structured logging

---

## Email System

### Configuration

**Development**: Gmail SMTP
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')  # App password
```

**Production**: SendGrid (recommended)
```python
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = env('SENDGRID_API_KEY')
```

### Email Utility

**Location**: `apps/families/emails.py`

**Function**: `send_family_invitation_email(invitation, request)`
- Generates absolute URL for invitation acceptance
- Renders HTML template with HaleWay branding
- Includes expiration date
- Returns True/False for success
- Logs all sends and failures

**Template**: `templates/families/emails/invitation_email.html`
- Responsive design (mobile + desktop)
- Ocean Blue (#2E86AB) and Palm Green (#06A77D) colors
- Plain text fallback

### Email Workflows

**Family Invitation**:
1. Admin sends invitation (POST `/families/<id>/invite/`)
2. System creates FamilyInvitation record with unique token
3. Email sent with acceptance link: `/families/invitation/<token>/accept/`
4. User clicks link:
   - If not logged in → redirect to login with ?next=
   - If logged in with wrong email → error message
   - If logged in with correct email → accept invitation → join family

---

## Integrations

### Mapbox Geocoding API

**Purpose**: Address autocomplete and coordinate lookup

**Usage**:
- Activity creation/editing (address search)
- Resort option creation (address search)
- Wishlist item creation (address search)

**Implementation**:
- JavaScript: `static/js/address-autocomplete.js`
- API Key: `MAPBOX_ACCESS_TOKEN` in settings
- Debounced search (300ms delay)
- Auto-populates: address_line1, city, state, zip_code, country, lat, long
- Calculates distance from resort using Haversine formula (Earth radius: 3959 miles)
- Estimates travel time (default: 40 mph average speed)

**AddressAutocomplete Class**:
```javascript
new AddressAutocomplete({
    searchInputId: 'address-search',
    addressFieldsMap: {
        address_line1: 'id_address_line1',
        city: 'id_city',
        state: 'id_state',
        zip_code: 'id_zip_code',
        country: 'id_country',
        latitude: 'id_latitude',
        longitude: 'id_longitude'
    },
    accessToken: MAPBOX_TOKEN
});
```

### Weather API

**Purpose**: 7-day weather forecast for trip destinations

**Usage**:
- Trip detail page (if resort has coordinates)
- Displays temperature range, conditions, weather icons
- Modal view for detailed daily breakdown

**Implementation**:
- Service: `apps/trips/services.py` → `WeatherService`
- API: weather.gov or alternative weather API
- Triggered: Automatically on trip detail page if lat/long exist
- Display: Mini forecast cards + detailed modal

### PWA (Progressive Web App)

**Purpose**: Mobile app-like experience

**Files**:
- `static/manifest.json` - App manifest
- `static/icons/` - Icon sizes (72x72 to 512x512)
- `templates/base.html` - Manifest link, meta tags

**Features**:
- Install as home screen app
- Offline access (future enhancement)
- Push notifications (future enhancement)

---

## Performance Optimizations

### Query Optimization

**select_related()**: Use for single-value foreign keys
```python
Trip.objects.select_related('family', 'resort', 'created_by')
```

**prefetch_related()**: Use for reverse foreign keys and many-to-many
```python
Trip.objects.prefetch_related('notes', 'activities', 'resort_options')
```

### Database Connection Pooling

**Production**: Use `django-db-conn-pool` or pgBouncer

### Caching Strategy

**Redis** (optional):
- Session storage
- Cache frequently accessed data (trip lists, family members)
- Cache duration: 5-15 minutes

### Static Files

**Development**: Django staticfiles
**Production**: WhiteNoise for serving static files

---

## Logging & Monitoring

### Structured Logging

**Library**: `structlog`

**Configuration**: `config/settings/base.py`

**Usage**:
```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("trip_created",
    trip_id=str(trip.id),
    family_id=str(family.id),
    created_by=user.username
)
```

**Log Locations**:
- Development: Console output (colored)
- Production: `logs/django.log` (JSON format)

**Search Logs**:
```bash
# Find all logs for specific user
grep '"user_id":"12345"' logs/django.log | jq .

# Find all error logs
grep '"level":"error"' logs/django.log | jq .
```

### Health Checks

**Package**: `django-health-check`

**Endpoints**:
- `/health/` - Overall health status (HTML)
- `/health/?format=json` - JSON health status

**Checks**:
- Database connectivity
- Migrations applied
- Storage access
- Cache (if enabled)

**Usage**:
- Docker healthcheck
- Kubernetes liveness probe
- Load balancer monitoring
- Uptime monitoring services

---

## Deployment Architecture

### Development

**Environment**: pyenv + local Django server
**Database**: PostgreSQL (local)
**Static Files**: Django staticfiles
**Email**: Gmail SMTP or console backend

### Production

**Environment**: Docker Compose
**Services**:
- `web`: Django app (Gunicorn)
- `db`: PostgreSQL 15
- `nginx`: Reverse proxy

**Deployment Script**: `./build.sh`
- Full rebuild: `./build.sh -r -d $(date +%Y%m%d)`
- Soft rebuild: `./build.sh -s`
- Backup only: `./build.sh -b -d $(date +%Y%m%d)`

**Static Files**: Collected with `python manage.py collectstatic`
**Migrations**: Run automatically in build.sh

---

## Security Considerations

### UUID Primary Keys
All models use UUID v4 for primary keys (non-guessable)

### CSRF Protection
All POST/PUT/DELETE requests require CSRF token

### SQL Injection Prevention
Django ORM prevents SQL injection via parameterized queries

### XSS Protection
Django templates auto-escape variables
Use `|safe` filter only when necessary

### Password Security
- Django's `pbkdf2_sha256` password hashing
- Minimum length validation
- Common password checking

### Email Security
- Gmail: App passwords (2FA required)
- SendGrid: API key authentication
- No plain text passwords in version control

---

This architecture document provides comprehensive technical details for developers working on HaleWay. For quick reference, see `CLAUDE.md`. For feature roadmap, see `docs/app_plan.md`.
