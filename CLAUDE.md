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
└── notes/          # Note and category management with search
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

### Important URLs
- **Admin**: `/admin/` - Django admin interface
- **Families**: `/families/` - Family management interface
- **Trips**: `/trips/` - Trip and resort management
- **Notes**: `/notes/` - Note and category management
- **Accounts**: `/accounts/` - User authentication and profiles

## Current Major Projects & Status

### 🚧 Active Development
**Phase 4: Activities** - Status: Planning
**Priority**: High
**Description**: Next phase - Activity creation with priority ordering and ratings
**Key Features**: Activity management, distance tracking, priority ordering, post-trip ratings
**Next Steps**: Create activities app, Activity model, priority ordering UI, ratings system

### 📋 Planned Features
**Phase 4**: Activities (Week 3-4) - Activity creation, priority ordering, ratings
**Phase 5**: Itinerary (Week 4) - Daily schedule planning with calendar view
**Phase 6**: Packing & Budget (Week 5) - Packing lists and budget tracking
**Phase 7-10**: See docs/app_plan.md for full roadmap

### ✅ Recently Completed
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

1. **Custom CSS System**: Never suggest Bootstrap/Tailwind - we have a complete custom system
2. **Mobile-First**: All UI decisions should start with mobile
3. **pyenv Development**: Local development uses pyenv, not Docker
4. **build.sh Deployment**: Production uses the build.sh script for all operations
5. **Domain Context**: [Add specific domain knowledge that AI should remember]
6. **Architecture Patterns**: [Key patterns to follow]
7. **Performance Requirements**: [Specific performance constraints]
8. **Security Requirements**: [Specific security considerations]

### Current Work Context
**Active Feature**: [What's currently being developed]  
**Blockers**: [Any current blockers or challenges]  
**Recent Changes**: [What was recently modified]  
**Next Priorities**: [What's coming up next]