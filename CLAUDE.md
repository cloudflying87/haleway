# CLAUDE.md - Project Memory & Context

**INSTRUCTIONS**: This is your project's living memory. Update this document as your project evolves. It serves as context for AI assistants and documentation for developers.

## Project Overview

**Project Name**: haleway
**Description**: HaleWay helps families plan vacations and preserve memories in one place. Organize activities, create itineraries, track budgets, and rate experiences. Share trips with your ohana and build a searchable archive of your family's favorite adventures.
**Industry/Domain**: travel
**Target Users**: travel lovers
**Current Status**: Development

### Quick Summary
HaleWay helps families plan vacations and preserve memories in one place. Organize activities, create itineraries, track budgets, and rate experiences. Share trips with your ohana and build a searchable archive of your family's favorite adventures.. Built for travel lovers in the travel industry.

## Key Architecture

### Backend Stack
- **Framework**: Django 5.0+ with Python 3.11+
- **Database**: PostgreSQL 15+
- **Cache**: Redis (optional)
- **Task Queue**: Celery (if needed)
- **Authentication**: Django built-in (customize as needed)

### Frontend Approach
- **Styling**: Custom CSS component system (NO Bootstrap/Tailwind)
- **JavaScript**: Vanilla JS or minimal framework
- **Design**: Mobile-first responsive design
- **Theme**: [Generated from style guide questionnaire]

### Infrastructure
- **Development**: pyenv + local Django server
- **Production**: Docker Compose with Nginx
- **Database**: PostgreSQL in production
- **Deployment**: Automated via build.sh script

## Current Major Components

### Apps Structure
```
apps/
├── core/           # Core functionality and homepage
├── accounts/       # Custom user authentication and profiles
├── families/       # Family management, invitations, and member roles
├── trips/          # Trip and resort management
├── notes/          # Note and category management with search
├── activities/     # Activity management with priority ordering
├── itinerary/      # Daily itinerary and schedule planning
├── packing/        # Packing list templates and trip packing lists
├── budget/         # Budget tracking and expense management
└── memories/       # Photos and journal entries (planned)
```

### Key Models
- **User** (accounts): Custom user model with email verification
- **Family** (families): Family group that can share trips
- **FamilyMember** (families): User membership in a family with roles (owner/admin/member)
- **FamilyInvitation** (families): Email-based family invitations with expiration
- **Trip** (trips): Vacation trip with dates, status, and destination
- **Resort** (trips): Lodging details with address and coordinates
- **NoteCategory** (notes): Category for organizing notes with color coding
- **Note** (notes): Trip notes with full-text search, pinning, and categorization
- **Activity** (activities): Trip activities with priority ordering and post-trip ratings
- **DailyItinerary** (itinerary): Scheduled items on specific days with timeline view
- **PackingListTemplate** (packing): Reusable packing list templates (system and custom)
- **PackingListTemplateItem** (packing): Items within packing templates
- **TripPackingList** (packing): Trip-specific packing lists (can be assigned to people)
- **TripPackingItem** (packing): Individual packing items with checkbox tracking
- **BudgetCategory** (budget): Category for organizing budget items with color coding
- **BudgetItem** (budget): Individual expenses with estimated/actual amounts and payment tracking

### Important URLs
- **Admin**: `/admin/` - Django admin interface
- **Families**: `/families/` - Family management interface
- **Trips**: `/trips/` - Trip and resort management
- **Notes**: `/notes/` - Note and category management
- **Activities**: `/activities/` - Activity management and planning
- **Itinerary**: `/itinerary/` - Daily schedule and itinerary planning
- **Packing**: `/packing/` - Packing list templates and trip packing lists
- **Budget**: `/budget/` - Budget tracking and expense management
- **Accounts**: `/accounts/` - User authentication and profiles

## Current Major Projects & Status

### 🚧 Active Development
**Phase 7-10: Advanced Features** - Status: In Progress
**Priority**: Medium
**Description**: Post-trip features, memories, and sharing functionality
**Next Steps**: See docs/app_plan.md for full roadmap

### 📋 Planned Features
**Phase 7**: Post-Trip Features - Trip photos, daily journals, memory preservation
**Phase 8-10**: See docs/app_plan.md for full roadmap

### ✅ Recently Completed
**Family Invitation Email System** - 2025-10-08 - Transactional email system complete
- Configured email backend with Gmail (dev) and SendGrid migration plan (prod)
- Created email utility module (apps/families/emails.py) for sending invitations
- Built responsive HTML email template using HaleWay color scheme
- Fixed accept_invitation view to handle unauthenticated users (redirect to login)
- Implemented case-insensitive email matching for invitations
- Enhanced form validation with user lookup (checks if email exists in database)
- Added detailed user feedback (already invited, already a member, account exists)
- Created comprehensive documentation in CLAUDE.md for Gmail and SendGrid setup
- Email template includes expiration date, family info, and responsive design
- Absolute URL generation for invitation links (works in dev and production)
- Structured logging for all email operations (send success/failure)
- Updated .env.example with full email configuration examples
- Supports both existing users (login to accept) and new users (register first)

**Budget Tracking** - 2025-10-08 - Trip expense tracking system complete
- Created budget app with 2 models (BudgetCategory, BudgetItem)
- Implemented budget category management with color coding
- Built budget item CRUD with estimated/actual amount tracking
- Created budget overview page with category grouping
- Developed automatic variance calculation (estimated vs actual)
- Implemented payment tracking (who paid, when, payment date)
- Added budget summary to trip detail page (inline preview)
- Built filtering by category and payment status
- Created comprehensive admin interface with variance display
- Database indexes for performance (trip, category, paid_by, payment_date)
- Structured logging for all budget operations
- Full permissions system (all members edit, admins delete)

**Phase 6: Packing Lists** - 2025-10-07 - Packing list management system complete
- Created packing app with 4 models (PackingListTemplate, PackingListTemplateItem, TripPackingList, TripPackingItem)
- Implemented reusable template system with 4 default templates (Beach, Mountains, Summer, Winter)
- Built template management views (list, detail, create, edit, delete)
- Created trip packing list views with template duplication
- Developed interactive checkbox UI with AJAX toggle for packed status
- Implemented "outfit calculator" feature (e.g., "5 outfits" = 5 shirts, 3 pants, 5 underwear, 5 socks)
- Added "save as template" feature to convert trip lists into reusable templates
- Created person assignment system for packing lists
- Built progress tracking with visual progress bars
- Integrated packing lists into trip detail page
- Added comprehensive admin interface with inline editing
- Database indexes for performance (trip, assigned_to, category, is_packed)
- Structured logging for all packing operations

**Phase 5: Itinerary** - 2025-10-07 - Daily itinerary planning system complete
- Created itinerary app with DailyItinerary model
- Implemented calendar view showing all trip dates with scheduled items
- Built day detail view with timeline visualization
- Created activity assignment functionality (assign existing activities to days/times)
- Developed quick-add feature for standalone events (breakfast, check-in, free time)
- Implemented itinerary item CRUD operations with proper permissions
- Created responsive calendar grid and timeline templates
- Added prev/next day navigation in day detail view
- Integrated with trip detail page
- Shows unscheduled activities for easy planning
- Supports all-day events and timed events
- Automatic ordering by time and custom order field
- Database indexes for performance (trip + date, trip + date + order)
- Structured logging for all itinerary operations

**Phase 4: Activities** - 2025-10-07 - Activity management system complete
- Created activities app with Activity model
- Implemented activity CRUD views with proper permissions
- Built activity list view with multiple sorting options (priority, name, distance, cost, rating, favorites)
- Created activity detail view with full information display
- Developed activity rating system for post-trip evaluation (1-5 stars, favorite flagging)
- Added manual distance entry field for activities
- Implemented drag-and-drop priority ordering UI with vanilla JavaScript
- Created responsive activity templates with mobile-first design
- Integrated activities with trip detail page
- Added indexes for performance optimization (trip + priority, trip + rating, trip + favorite)
- Structured logging for all activity operations

**Phase 3: Notes System** - 2025-10-07 - Categorized notes system complete
- Created notes app with NoteCategory and Note models
- Implemented full-text search on note title and content (PostgreSQL)
- Built category management (create/edit/delete with color coding)
- Added note pinning feature for important notes
- Created note CRUD views with proper permissions
- Integrated notes with trip management
- Added search and filtering capabilities

**Phase 2: Core Trip Management** - 2025-10-07 - Trip planning system complete
- Created trips app with Trip and Resort models
- Built trip creation form with optional resort details
- Implemented trip list views (all trips + family-specific)
- Created trip detail page with resort information display
- Added trip/resort editing with proper permissions
- Integrated trips with family management
- Duration calculation and date validation

**Phase 1: Foundation** - 2025-10-07 - Family management system complete
- Created families app with Family, FamilyMember, and FamilyInvitation models
- Built family creation, invitation, and member management views
- Implemented role-based permissions (owner/admin/member)
- Created responsive templates with HaleWay color scheme
- Added structured logging throughout

## Database Schema Context

### Core Models
```python
# Key model relationships and constraints

Family:
  - UUID primary key
  - name: Family display name
  - Relationships: Has many FamilyMembers, has many FamilyInvitations
  - Business rules: Must have exactly one owner
  - Methods: get_owner(), get_admins(), get_all_members()

FamilyMember:
  - UUID primary key
  - Unique constraint: (family, user)
  - role: owner/admin/member (only one owner per family)
  - Indexes: (family, role)
  - Business rules: Cannot remove family owner
  - Methods: is_owner(), is_admin(), can_manage_members()

FamilyInvitation:
  - UUID primary key
  - Unique token for accepting invitation
  - status: pending/accepted/expired
  - expires_at: Auto-set to 7 days from creation
  - Indexes: (family, status), (email, status), (token)
  - Methods: is_valid(), mark_accepted(), mark_expired()

Trip:
  - UUID primary key
  - family: Foreign key to Family
  - name, destination_name: Trip identification
  - start_date, end_date: Trip dates
  - status: planning/active/completed
  - Indexes: (family, status), (start_date)
  - Methods: duration_days(), is_upcoming(), is_active(), is_past()

Resort:
  - UUID primary key (one-to-one with Trip)
  - Full address fields with optional lat/long
  - general_notes: TextField for confirmation numbers, etc.

NoteCategory:
  - UUID primary key
  - trip: Foreign key to Trip
  - name: Category display name
  - color_code: Hex color for UI organization
  - order: Integer for sorting
  - Unique constraint: (trip, name)
  - Indexes: (trip, order)

Note:
  - UUID primary key
  - trip: Foreign key to Trip
  - category: Foreign key to NoteCategory (nullable)
  - title, content: Note text
  - is_pinned: Boolean for important notes
  - search_vector: Full-text search field (PostgreSQL)
  - Indexes: (trip, category), (trip, is_pinned), GIN index on search_vector
  - Ordering: Pinned notes first, then by updated_at

Activity:
  - UUID primary key
  - trip: Foreign key to Trip
  - name, description: Activity identification
  - Full address fields with optional lat/long
  - distance_from_resort: Decimal (manual entry, miles)
  - estimated_cost, estimated_duration: Planning fields
  - pre_trip_priority: Integer for ranking (0 = unranked, lower = higher priority)
  - post_trip_rating: Integer 1-5 (nullable, for post-trip evaluation)
  - post_trip_notes: TextField (nullable)
  - is_favorite: Boolean flag for "would do again"
  - Indexes: (trip, pre_trip_priority), (trip, post_trip_rating), (trip, is_favorite)
  - Ordering: By pre_trip_priority, then created_at
  - Methods: has_rating(), get_duration_display(), get_full_address()

PackingListTemplate:
  - UUID primary key
  - name, description: Template identification
  - is_system_template: Boolean (prevents deletion of built-in templates)
  - created_by: Foreign key to User (nullable for system templates)
  - Ordering: By name
  - Methods: duplicate_for_trip(trip, assigned_to, list_name) - Creates TripPackingList instance

PackingListTemplateItem:
  - UUID primary key
  - template: Foreign key to PackingListTemplate
  - category: CharField for grouping (e.g., Clothing, Electronics)
  - item_name, quantity, notes: Item details
  - order: Integer for custom sorting within category
  - Indexes: (template, category)
  - Ordering: By category, order, item_name

TripPackingList:
  - UUID primary key
  - trip: Foreign key to Trip
  - name: List identification (e.g., "David's List", "Beach Gear")
  - based_on_template: Foreign key to PackingListTemplate (nullable)
  - assigned_to: Foreign key to User (nullable - can assign to family member)
  - Indexes: (trip), (assigned_to)
  - Ordering: By name
  - Methods: get_packed_percentage(), get_packed_count(), get_total_count(), save_as_template()

TripPackingItem:
  - UUID primary key
  - packing_list: Foreign key to TripPackingList
  - category: CharField for grouping
  - item_name, quantity, notes: Item details
  - is_packed: Boolean checkbox state
  - order: Integer for custom sorting
  - Indexes: (packing_list, category), (packing_list, is_packed)
  - Ordering: By category, order, item_name
```

### Important Relationships
- Family → FamilyMember: One-to-many (a family has many members)
- User → FamilyMember: One-to-many (a user can be in multiple families)
- Family → FamilyInvitation: One-to-many (a family can have many invitations)
- User → FamilyInvitation: One-to-many via invited_by (a user can send many invitations)
- Family → Trip: One-to-many (a family can have many trips)
- Trip → Resort: One-to-one (a trip has one resort)
- Trip → NoteCategory: One-to-many (a trip can have many categories)
- Trip → Note: One-to-many (a trip can have many notes)
- NoteCategory → Note: One-to-many (a category can have many notes)
- Trip → Activity: One-to-many (a trip can have many activities)
- User → Activity: One-to-many via created_by (a user can create many activities)
- PackingListTemplate → PackingListTemplateItem: One-to-many (a template has many items)
- Trip → TripPackingList: One-to-many (a trip can have many packing lists)
- User → TripPackingList: One-to-many via assigned_to (a user can be assigned many lists)
- PackingListTemplate → TripPackingList: One-to-many via based_on_template (template can spawn many lists)
- TripPackingList → TripPackingItem: One-to-many (a packing list has many items)

## Custom CSS System

### Theme Configuration
Based on questionnaire answers in `docs/STYLE_GUIDE.md`:

- **Primary Color**: #2e86ab - [Usage description]
- **Secondary Color**: #2e86ab - [Usage description]
- **Accent Color**: #2e86ab - [Usage description]
- **Design Style**: Friendly
- **Border Radius**: 8px

### Component Architecture
```
static/css/
├── base.css              # CSS variables, typography, utilities
├── components/           # Reusable components
│   ├── buttons.css      # Button variants and states
│   ├── forms.css        # Form controls and layouts
│   ├── cards.css        # Card components
│   ├── modals.css       # Modal dialogs
│   └── tables.css       # Data table styles
└── apps/                # App-specific styles
    ├── [app_name].css   # App-specific styling
    └── [app_name].css   # App-specific styling
```

### Key CSS Patterns
- **Mobile-First**: All components start with mobile styles
- **CSS Variables**: Consistent theming with `var(--color-primary)`
- **BEM Methodology**: `.component__element--modifier` naming
- **Responsive**: Breakpoints at 576px, 768px, 992px, 1200px

## Development Workflow

### Daily Development
```bash
# Start development session
pyenv activate haleway
python manage.py runserver

# Common tasks
python manage.py makemigrations
python manage.py migrate
python manage.py shell
python manage.py test
```

### Production Deployment
```bash
# Full rebuild with backup
./build.sh -r -d $(date +%Y%m%d)

# Soft rebuild (preserve database)
./build.sh -s

# Backup only
./build.sh -b -d $(date +%Y%m%d)
```

### Code Quality (Modern Tooling)
```bash
# Format and lint with ruff (10-100x faster than black+isort+flake8)
make format      # Auto-format code
make lint        # Check code quality
make type-check  # Type checking with mypy
make security    # Security scan with bandit
make quality     # Run all checks

# Check migrations for unsafe operations
make check-migrations

# Test with coverage
pytest --cov=apps

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### File Encoding Standards

**CRITICAL: All files MUST be UTF-8 encoded**

This project requires UTF-8 encoding for all files, especially templates. Failure to use UTF-8 will cause `UnicodeDecodeError` when Django tries to render templates.

**Best Practices:**
- ✅ **Always use UTF-8 encoding** when creating new files
- ✅ **Avoid emojis in template files** - Use HTML entities or Font Awesome icons instead
- ✅ **If using emojis, ensure file is saved as UTF-8**
- ❌ **Never use ISO-8859-1, Windows-1252, or other encodings**

**How to Check File Encoding:**
```bash
# Check a file's encoding
file -b --mime-encoding path/to/file.html

# Convert a file from ISO-8859-1 to UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.html > output.html
```

**Common Error:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb0 in position X
```
This means a file is not UTF-8 encoded. Use the commands above to check and fix.

**Editor Configuration:**
- VS Code: Add to settings.json: `"files.encoding": "utf8"`
- PyCharm: Settings → Editor → File Encodings → set to UTF-8
- Vim: Add to .vimrc: `set encoding=utf-8 fileencoding=utf-8`

## Logging Best Practices

**This project uses structlog for structured logging. Always use this pattern:**

### Correct Logging Pattern
```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ CORRECT - Structured logging with context
logger.info("user_login_success", user_id=user.id, username=user.username, ip=request.META.get('REMOTE_ADDR'))
logger.warning("payment_failed", user_id=user.id, amount=amount, reason="insufficient_funds")
logger.error("database_connection_failed", host=db_host, port=db_port, exc_info=True)

# ✅ Adding persistent context
logger = logger.bind(user_id=user.id, request_id=request_id)
logger.info("order_created", order_id=order.id)  # user_id and request_id auto-included

# ✅ Exception logging
try:
    process_payment(order)
except PaymentError as e:
    logger.exception("payment_processing_error", order_id=order.id, amount=order.total)
```

### ❌ WRONG - Don't Do This
```python
# ❌ String formatting loses structure
logger.info(f"User {user.username} logged in from {ip}")

# ❌ No context data
logger.info("Payment failed")

# ❌ Old-style formatting
logger.info("Order %s created by user %s", order.id, user.id)
```

### Why Structured Logging?
- **Searchable**: Query logs by `user_id`, `order_id`, etc.
- **Parseable**: JSON output for log aggregators (ELK, Datadog, etc.)
- **Contextual**: Automatic request_id, user_id tracking
- **Performant**: Faster than string formatting
- **Debuggable**: See all related logs instantly

### Log Levels
- **DEBUG**: Detailed diagnostic info (dev only)
- **INFO**: Important business events (`user_registered`, `order_completed`)
- **WARNING**: Recoverable issues (`rate_limit_approached`, `cache_miss`)
- **ERROR**: Errors that need attention (`payment_failed`, `email_send_error`)
- **CRITICAL**: System failures (`database_down`, `out_of_memory`)

### Viewing Logs
```bash
# Development: Colored console output
make run

# Production: JSON logs in logs/django.log
tail -f logs/django.log | jq .  # Pretty-print JSON

# Search logs
grep "user_id.*12345" logs/django.log | jq .
```

## Email Configuration & Family Invitations

**This project sends transactional emails for family invitations. Email setup is required for invitations to work.**

### Current Setup (Development - Gmail)

The project is currently configured to use Gmail SMTP for development. To enable email sending:

1. **Enable 2-Factor Authentication** on your Google account:
   - Visit: https://myaccount.google.com/security
   - Turn on 2-Step Verification

2. **Create App Password**:
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (custom name)"
   - Enter "HaleWay Django" and click Generate
   - Copy the 16-character password

3. **Update `.env` file**:
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your.email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password-here
   DEFAULT_FROM_EMAIL=your.email@gmail.com
   ```

4. **Test email sending**:
   ```bash
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'It works!', 'your@gmail.com', ['recipient@email.com'])
   ```

**Gmail Limitations:**
- **500 emails/day** for free Gmail accounts
- **2000 emails/day** for Google Workspace accounts
- Emails may be flagged as spam
- Not suitable for production

---

### Production Setup (SendGrid - Recommended)

For production, migrate to SendGrid for better deliverability and higher limits.

**Why SendGrid?**
- **100 emails/day free** (perfect for family app)
- Excellent deliverability (won't go to spam)
- Easy setup (15 minutes)
- Analytics dashboard
- Scales to $20/month for 50k emails

**Migration Steps:**

1. **Sign up for SendGrid**:
   - Visit: https://sendgrid.com/
   - Create free account
   - Verify your email address

2. **Create API Key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Choose "Full Access"
   - Copy the key (shown only once!)

3. **Verify Sender Identity** (Required for production):
   - Go to Settings → Sender Authentication
   - Choose "Single Sender Verification" (easiest)
   - Add: `noreply@haleway.flyhomemnlab.com`
   - Click verification link in email

4. **Update Production `.env`**:
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxx  # Your API key
   DEFAULT_FROM_EMAIL=noreply@haleway.flyhomemnlab.com
   ```

5. **Test in Production**:
   ```bash
   # SSH into production server
   docker compose exec web python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Production email!', 'noreply@haleway.flyhomemnlab.com', ['your@email.com'])
   ```

6. **Monitor Delivery**:
   - SendGrid Dashboard: https://app.sendgrid.com/
   - View delivery stats, opens, clicks
   - Check for bounces and spam reports

**SendGrid Best Practices:**
- Use `noreply@yourdomain.com` for transactional emails
- Verify your domain (optional, for higher limits)
- Enable click/open tracking in SendGrid settings
- Monitor bounce rates (should be < 5%)
- Add unsubscribe links if sending marketing emails

---

### How Family Invitations Work

**Invitation Flow:**

1. **Admin invites user** → `POST /families/{id}/invite/`
   - Creates `FamilyInvitation` record with unique token
   - Sends email with acceptance link
   - Email contains: `/families/invitation/{token}/accept/`

2. **User clicks link**:
   - **If not logged in**: Redirect to login with `?next=` parameter
   - **If logged in with wrong email**: Show error message
   - **If logged in with correct email**: Accept invitation → Join family

3. **User lookup logic**:
   - System checks if email exists in database
   - **User exists**: They just need to log in
   - **User doesn't exist**: They need to create account first
   - Both cases are handled seamlessly

**Email Template:**
- Location: `templates/families/emails/invitation_email.html`
- Uses HaleWay color scheme (Ocean Blue #2E86AB, Palm Green #06A77D)
- Responsive design for mobile/desktop
- Includes expiration date (7 days from creation)
- Plain text fallback for email clients

**Email Utility:**
- Location: `apps/families/emails.py`
- Function: `send_family_invitation_email(invitation, request)`
- Handles absolute URL generation
- Logs all email sends and failures
- Returns `True` if successful, `False` if failed

**Testing Invitations:**
```bash
# 1. Start development server
python manage.py runserver

# 2. Create a family and invite a user
# 3. Check console for email output (if using console backend)
# 4. Copy the invitation URL from console
# 5. Open in browser to test acceptance flow
```

**Troubleshooting:**
- **Email not sending**: Check `EMAIL_BACKEND` in `.env`
- **Console backend**: Emails print to console (development only)
- **SMTP errors**: Verify Gmail app password or SendGrid API key
- **Wrong email error**: User must log in with invited email address
- **Expired invitation**: Create new invitation (7 day limit)

---

## Health Checks & Monitoring

### Health Check Endpoints
The project includes django-health-check for monitoring:

```python
# Add to config/urls.py:
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('health/', include('health_check.urls')),
]
```

### Available Endpoints
- `/health/` - Overall health status
- `/health/?format=json` - JSON health status

### Checks Included
- **Database**: Connection and query test
- **Cache**: Redis connectivity (if enabled)
- **Storage**: Disk space and file system

### Using Health Checks
```bash
# Check health (server must be running)
make health

# Or manually
curl http://localhost:8000/health/
```

### Production Monitoring
Use `/health/` for:
- **Docker health checks** in docker-compose.yml
- **Kubernetes liveness probes**
- **Load balancer health monitoring**
- **Uptime monitoring services** (UptimeRobot, Pingdom, etc.)

## Modern Tools Included

### Browser Auto-Reload (Development)
- **Package**: django-browser-reload
- **What it does**: Auto-refreshes browser when you save code
- **Setup**: Already configured in development settings
- **No action needed**: Just save your files and watch the magic!

### Migration Safety
- **Package**: django-migration-linter
- **What it does**: Catches unsafe migration operations
- **Prevents**: Adding non-nullable columns, dropping tables without backup, etc.
- **Usage**: Runs automatically in pre-commit hooks
- **Manual check**: `make check-migrations`

### HTTP Client
- **Package**: httpx
- **Use for**: Making API calls (replaces requests)
- **Benefits**: Async support, HTTP/2, connection pooling

```python
import httpx

# Sync usage (like requests)
response = httpx.get('https://api.example.com/data')

# Async usage (in async views)
async with httpx.AsyncClient() as client:
    response = await client.get('https://api.example.com/data')
```

## Domain-Specific Context

### [CUSTOMIZE THIS SECTION FOR YOUR DOMAIN]

#### For Aviation Projects:
- **Regulatory Context**: FAR compliance requirements
- **Data Validation**: Flight time limits, currency requirements
- **Safety Considerations**: Audit trails, data integrity
- **Key Calculations**: Flight time, currency, duty limits

#### For Healthcare Projects:
- **Compliance**: HIPAA requirements
- **Data Security**: Patient data protection
- **Audit Requirements**: Complete audit trails
- **Key Features**: Patient records, appointments, billing

#### For E-commerce Projects:
- **Payment Processing**: Stripe/PayPal integration
- **Inventory Management**: Stock tracking
- **Order Fulfillment**: Shipping integration
- **Customer Experience**: Reviews, recommendations

#### For Financial Projects:
- **Compliance**: SOX, financial regulations
- **Security**: Encryption, secure transactions
- **Reporting**: Financial statements, analytics
- **Integration**: Banking APIs, payment processors

## Technical Decisions & Rationale

### Architecture Decisions
**Decision**: [e.g., "Custom CSS instead of Bootstrap"]
**Rationale**: [Why this decision was made]
**Trade-offs**: [What was gained/lost]
**Date**: [When decided]

**Decision**: [e.g., "pyenv for development, Docker for production"]
**Rationale**: [Why this decision was made]
**Trade-offs**: [What was gained/lost]
**Date**: [When decided]

### Technology Choices
**Database**: PostgreSQL - [Why PostgreSQL over alternatives]
**Cache**: [Redis/None] - [Caching strategy and reasoning]
**Frontend**: Custom CSS - [Why no frameworks]
**Testing**: pytest + Django Test - [Testing approach]

## Performance Considerations

### Database Optimization
- **Indexes**: [List important indexes and why]
- **Query Optimization**: [Key querysets with select_related/prefetch_related]
- **Caching Strategy**: [What's cached and for how long]

### Frontend Performance
- **CSS**: [Minification, critical path CSS]
- **JavaScript**: [Bundling, async loading strategies]
- **Images**: [Optimization, responsive images]
- **Mobile**: [Specific mobile performance considerations]

## Security Implementation

### Authentication & Authorization
- **User Model**: [Custom user model or Django default]
- **Permissions**: [Permission system approach]
- **Sessions**: [Session configuration]

### Data Protection
- **Input Validation**: [Validation approach and tools]
- **SQL Injection**: [Prevention methods]
- **XSS Protection**: [Template escaping, CSP headers]
- **CSRF**: [CSRF token implementation]

### [Domain-Specific Security]
- **[Industry requirement]**: [How it's implemented]
- **[Compliance standard]**: [How it's met]

## Integration Points

### External Services
**Service**: [e.g., Email provider] - [How it's used]
**Service**: [e.g., Payment processor] - [How it's used]
**Service**: [e.g., Maps API] - [How it's used]

### APIs
**Internal API**: [Description of your API endpoints]
**External APIs**: [Third-party APIs you consume]

## Deployment & Infrastructure

### Environment Configuration
```bash
# Required environment variables
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=project_db
DB_USER=project_user
DB_PASSWORD=secure-password
# [Add other required vars]
```

### Production Setup
- **Server**: [Hosting provider/setup]
- **Database**: [PostgreSQL configuration]
- **Static Files**: [WhiteNoise/CDN setup]
- **SSL**: [Certificate setup]
- **Monitoring**: [Error tracking, performance monitoring]

### Backup Strategy
- **Database**: Automated daily backups via build.sh
- **Media Files**: [Backup strategy for user uploads]
- **Code**: Git repository + [additional backup if any]

## Testing Strategy

### Test Coverage
- **Models**: [Coverage level and key test cases]
- **Views**: [Coverage level and key test cases]
- **Forms**: [Coverage level and key test cases]
- **Integration**: [Key user workflows tested]

### Test Data
- **Factories**: [Factory classes for test data]
- **Fixtures**: [Static test data files]
- **Test Database**: [Test database configuration]

## Common Issues & Solutions

### Development Issues
**Issue**: [Common problem]
**Solution**: [How to fix it]
**Prevention**: [How to avoid it]

**Issue**: [Common problem]
**Solution**: [How to fix it]
**Prevention**: [How to avoid it]

### Production Issues
**Issue**: [Common problem]
**Solution**: [How to fix it]
**Monitoring**: [How to detect it early]

## Quick Reference Commands

### Development
```bash
# Create new app
python manage.py startapp [app_name]

# Database operations
python manage.py makemigrations [app_name]
python manage.py migrate
python manage.py dbshell

# User management
python manage.py createsuperuser
python manage.py changepassword [username]

# Development server
python manage.py runserver
python manage.py runserver 0.0.0.0:8000  # For external access
```

### Production
```bash
# Deploy with backup/restore
./build.sh -r -d YYYYMMDD

# Backup database
./build.sh -b -d $(date +%Y%m%d)

# Soft rebuild (preserve data)
./build.sh -s

# View logs
docker compose logs -f web
docker compose logs -f db
```

### Debugging
```bash
# Django shell with extensions
python manage.py shell_plus

# Database queries debug
python manage.py shell_plus --print-sql

# Show URLs
python manage.py show_urls
```

## File Structure Reference

### Key Files & Directories
```
project_name/
├── CLAUDE.md                    # This file - project memory
├── build.sh                     # Production deployment script
├── manage.py                    # Django management
├── requirements/                # Python dependencies
│   ├── base.txt                # Core requirements
│   ├── development.txt         # Dev-only requirements
│   └── production.txt          # Production requirements
├── config/                     # Django project configuration
│   ├── settings/               # Environment-specific settings
│   ├── urls.py                 # Main URL configuration
│   └── wsgi.py                 # WSGI configuration
├── apps/                       # Django applications
├── static/                     # Static files (CSS, JS, images)
├── templates/                  # Django templates
├── media/                      # User uploads
├── docs/                       # Documentation
│   ├── STYLE_GUIDE.md         # Project style guide
│   └── CODING_GUIDE.md        # Development standards
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── docker-compose.yml          # Production containers
├── Dockerfile                  # Production image
├── .env.example               # Environment variables template
└── .gitignore                 # Git ignore rules
```

## Project History & Evolution

### Version History
**v1.0** - 2025-10-07 - [Initial release with core features]
**v1.1** - 2025-10-07 - [Major feature additions]
**v1.2** - 2025-10-07 - [Performance improvements, bug fixes]

### Major Milestones
- **2025-10-07**: Project started
- **2025-10-07**: [Significant milestone]
- **2025-10-07**: [Production deployment]
- **2025-10-07**: [Major feature launch]

## Team & Contacts

### Key People
**Developer**: [Name/Contact]
**Designer**: [Name/Contact] (if applicable)
**Product Owner**: [Name/Contact] (if applicable)

### External Contacts
**Hosting Provider**: [Contact info]
**Domain Registrar**: [Contact info]
**Third-party Services**: [List with contacts]

---

## Maintenance Notes

### Regular Tasks
- **Weekly**: Review error logs, check performance metrics
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Full backup verification, security audit

### Update Log
**2025-10-07**: [What was updated/changed]
**2025-10-07**: [What was updated/changed]
**2025-10-07**: [What was updated/changed]

---

*Last Updated: 2025-10-07*
*Next Major Review: 2025-10-07*
*Current Focus: [What you're working on]*

## Context for AI Assistants

When working with this project, remember:

1. **UTF-8 Encoding REQUIRED**: All files MUST be UTF-8 encoded. Never create files with ISO-8859-1 or other encodings. Avoid emojis in templates or ensure UTF-8 encoding if used.
2. **Custom CSS System**: Never suggest Bootstrap/Tailwind - we have a complete custom system
3. **Mobile-First**: All UI decisions should start with mobile
4. **pyenv Development**: Local development uses pyenv, not Docker
5. **build.sh Deployment**: Production uses the build.sh script for all operations
6. **Structured Logging**: Always use structlog with key-value pairs, never string formatting
7. **Architecture Patterns**: Follow existing patterns in similar apps (notes, activities, etc.)
8. **Security Requirements**: All family members can edit, only admins can delete

### Current Work Context
**Active Feature**: [What's currently being developed]
**Blockers**: [Any current blockers or challenges]
**Recent Changes**: [What was recently modified]
**Next Priorities**: [What's coming up next]
