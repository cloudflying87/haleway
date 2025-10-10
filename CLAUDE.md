# CLAUDE.md - Project Quick Reference

**Last Updated**: 2025-10-09
**Current Status**: Production Ready - Phase 11 Complete

## Project Overview

**HaleWay** - Family vacation planning and memory preservation platform
**Stack**: Django 5.0+ | PostgreSQL 15+ | Vanilla JS | Custom CSS
**Stage**: 11 apps, ~25 models, 100+ views, fully functional

### What Makes This Project Special
- **Structured Logging**: `structlog` throughout (searchable, parseable)
- **Modern Tooling**: ruff (formatting/linting), pre-commit hooks, health checks
- **Mobile-First**: Responsive design, collapsible sections, PWA support
- **Security**: UUID primary keys, role-based permissions, proper CSRF
- **Performance**: Strategic indexes, select_related/prefetch_related

## Quick Start

```bash
# Development
pyenv activate haleway
python manage.py runserver

# Production Deployment
./build.sh -r -d $(date +%Y%m%d)  # Full rebuild with backup
./build.sh -s                      # Soft rebuild (preserve DB)

# Code Quality
make format      # Auto-format with ruff
make lint        # Check code quality
make test        # Run tests with coverage
```

## Core Architecture

### Apps Structure
```
apps/
├── core/           # Homepage, dashboard, shared utilities
├── accounts/       # Custom user auth, profiles
├── families/       # Family management, invitations, roles
├── trips/          # Trip planning, resorts, dream trips
├── notes/          # Categorized notes with full-text search
├── activities/     # Activity planning with ratings
├── itinerary/      # Daily schedule planning
├── packing/        # Packing lists with templates
├── grocery/        # Grocery lists with templates
├── budget/         # Expense tracking and budgeting
└── memories/       # Photos and daily journals
```

### Key Models (Simplified)
- **Family** → **FamilyMember** (roles: owner/admin/member) → **FamilyInvitation**
- **Trip** (planning/active/completed/dream) → **Resort** (one-to-one)
- **Trip** → **TripResortOption** (many, for dream trips)
- **Family** → **ResortWishlist** (many, research collection)
- **Trip** → **Note**, **Activity**, **DailyItinerary**, **BudgetItem**, **TripPackingList**, **TripGroceryList**, **TripPhoto**, **DailyJournal**
- **PackingListTemplate** / **GroceryListTemplate** (reusable)

### Important URLs
- `/admin/` - Django admin
- `/families/` - Family management
- `/trips/` - Trip planning
- `/trips/wishlist/` - Resort wishlist
- `/trips/<id>/resort-options/` - Dream trip resort comparison
- `/activities/<trip_id>/` - Activities
- `/itinerary/<trip_id>/calendar/` - Daily itinerary
- `/packing/<trip_id>/` - Packing lists
- `/grocery/trip/<trip_id>/` - Grocery lists
- `/budget/<trip_id>/` - Budget tracking
- `/memories/<trip_id>/photos/` - Photo gallery
- `/memories/<trip_id>/journal/` - Daily journal

## Critical Configuration

### UTF-8 Encoding (CRITICAL)
**All files MUST be UTF-8 encoded.** Django will throw `UnicodeDecodeError` otherwise.

```bash
# Check encoding
file -b --mime-encoding path/to/file.html

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 input.html > output.html
```

### Structured Logging (REQUIRED)
Always use key-value pairs, never string formatting:

```python
import structlog
logger = structlog.get_logger(__name__)

# ✅ CORRECT
logger.info("user_login", user_id=user.id, ip=request.META['REMOTE_ADDR'])

# ❌ WRONG
logger.info(f"User {user.id} logged in from {ip}")
```

### Email Configuration
**Development**: Gmail SMTP (see `.env.example`)
**Production**: SendGrid recommended (100/day free)

```bash
# .env settings
EMAIL_HOST=smtp.gmail.com  # or smtp.sendgrid.net
EMAIL_HOST_USER=your@email.com  # or 'apikey' for SendGrid
EMAIL_HOST_PASSWORD=app-password  # or SendGrid API key
DEFAULT_FROM_EMAIL=noreply@haleway.com
```

## Development Workflow

### File Encoding Standards
- **Always use UTF-8** when creating files
- **Avoid emojis** in templates (use HTML entities or Font Awesome)
- **Check encoding** before committing: `file -b --mime-encoding file.html`

### Custom CSS System
- **NO Bootstrap or Tailwind** - we have a complete custom component system
- **Mobile-first** - all breakpoints use `min-width`
- **BEM naming** - `.component__element--modifier`
- **CSS variables** - `var(--primary-color)` for theming
- **Components**: `static/css/components/*.css`

See `docs/STYLE_GUIDE.md` for form patterns and component guidelines.

### Pre-commit Hooks
Automatically run on `git commit`:
- `ruff format` - Auto-format Python code
- `ruff check --fix` - Fix linting issues
- `python-check-blanket-noqa` - Prevent blanket noqa
- `python-check-mock-methods` - Validate mocks
- `django-migration-linter` - Catch unsafe migrations

### Common Tasks

```bash
# Django Management
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell_plus  # Enhanced shell

# Code Quality
make format           # Format with ruff
make lint            # Check code quality
make type-check      # Type checking with mypy
make security        # Security scan with bandit
make quality         # Run all checks
make check-migrations # Check for unsafe migrations

# Testing
pytest                       # Run tests
pytest --cov=apps           # With coverage
make test                   # Run tests via Makefile

# Health Check
make health  # Check app health at /health/

# Git Operations
# NEVER use --no-verify or --amend (unless explicitly requested)
# ALWAYS check authorship before amending: git log -1 --format='%an %ae'
```

## Feature Implementation Status

### ✅ Completed (Phases 1-11)
- **Phase 1-2**: Families, trips, resorts
- **Phase 3**: Notes with full-text search
- **Phase 4**: Activities with ratings
- **Phase 5**: Daily itinerary
- **Phase 6**: Packing lists with templates
- **Phase 7**: Photos and journals
- **Budget**: Expense tracking (Phase 6+)
- **Navigation**: Collapsible sections, quick nav
- **Phase 11**: Grocery lists, dream trips, resort wishlist

### 🎯 Next Priorities (Phase 8+)
1. **Enhanced Dashboard** - Recent photos, upcoming trips, stats
2. **Global Search** - Search across all trips/activities/notes
3. **Activity Tags** - Categorize and filter activities
4. **Trip Templates** - Save and clone trip structures
5. **Email Notifications** - Trip reminders, packing alerts

See `docs/app_plan.md` for complete roadmap.

## Database Schema Summary

Full schema in `docs/ARCHITECTURE.md`. Key relationships:

- Family (1) → FamilyMember (N) → User
- Family (1) → Trip (N)
- Trip (1) → Resort (1), but Trip (1) → TripResortOption (N) for dream trips
- Family (1) → ResortWishlist (N) - research collection
- Trip (1) → [Notes, Activities, Itinerary, Packing, Grocery, Budget, Photos, Journals] (N)
- Templates: PackingListTemplate, GroceryListTemplate (reusable)

**All tables use UUID primary keys for security.**

## Important Patterns

### Permission System
- **All family members**: Create and edit items
- **Admins only**: Delete items, manage categories
- **Creators**: Can edit/delete their own content

### Form Styling (Modern Pattern)
All item forms (packing, grocery, etc.) use consistent styling:
- Select2 category dropdown (searchable, create-new)
- Modern card layout with gradient shadows
- Breadcrumb navigation
- Quick Tips informational boxes
- Auto-focus on primary field

See `apps/grocery/templates/grocery/item_form.html` for reference.

### Modal UI Pattern
- AJAX submission without page reload
- Select2 integration for dropdowns
- Category pre-fill from context
- Success/error feedback

## Troubleshooting

### Common Issues

**UnicodeDecodeError in templates**
- **Cause**: File not UTF-8 encoded
- **Fix**: `iconv -f ISO-8859-1 -t UTF-8 input.html > output.html`

**Email not sending**
- **Dev**: Check `EMAIL_BACKEND` in `.env`, verify Gmail app password
- **Prod**: Verify SendGrid API key, check sender verification

**Migration conflicts**
- **Check**: `python manage.py showmigrations`
- **Fix**: Resolve conflicts manually or use `python manage.py migrate --fake-initial`

**Debug toolbar issues in tests**
- **Check**: `config/settings/development.py` - ensure proper test exclusion

### Health Monitoring
```bash
# Check system health
curl http://localhost:8000/health/

# View logs
docker compose logs -f web  # Production
tail -f logs/django.log     # Local

# Search logs (structured)
grep "user_id.*12345" logs/django.log | jq .
```

## Git Commit Guidelines

**NEVER**:
- Update git config
- Use `--no-verify`, `--no-gpg-sign`
- Force push to main/master
- Amend commits from other developers

**Commit Message Format**:
```
Brief description of changes

More details if needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Documentation Structure

- **CLAUDE.md** (this file) - Quick reference, core info
- **docs/app_plan.md** - Feature roadmap, implementation phases
- **docs/ARCHITECTURE.md** - Technical details, models, indexes
- **docs/STYLE_GUIDE.md** - CSS patterns, form styling, components
- **.env.example** - Environment variable template

## Key Wins & Differentiators

1. **Structured Logging** - Makes debugging trivial
2. **Modern Tooling** - ruff is 10-100x faster than black+isort+flake8
3. **Custom CSS** - Complete control, no framework bloat
4. **Mobile-First** - Truly responsive, not desktop-first
5. **UUID PKs** - Security by design
6. **Pre-commit Hooks** - Catch issues before commit
7. **Health Checks** - Production monitoring ready
8. **PWA Support** - Mobile app-like experience

## Contact & Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues (configure in repo)
- **Help**: `/help` command in Claude Code CLI

---

**Remember**: This project uses structured logging, UTF-8 encoding, and custom CSS. Always follow established patterns for consistency.
