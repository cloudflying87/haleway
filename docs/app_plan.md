# HaleWay - Database Schema & Implementation Plan

## Color Scheme

**Primary palette:**
- **Ocean Blue**: #2E86AB (trust, calm, travel-friendly)
- **Sunset Coral**: #FF6B6B (warm, energetic, fun)
- **Sandy Beige**: #F4E8C1 (neutral, easy on eyes)
- **Palm Green**: #06A77D (accent, fresh, adventurous)

**Neutrals:**
- Dark text: #2C3E50
- Light background: #F8F9FA
- Borders/dividers: #E0E0E0

---

## Database Schema

### User & Family Management

#### Family
- id (Primary Key)
- name (e.g., "The Smith Family")
- created_at
- updated_at

#### FamilyMember
- id (Primary Key)
- family_id (Foreign Key → Family)
- user_id (Foreign Key → Django User)
- role (choices: 'owner', 'admin', 'member')
- joined_at

#### FamilyInvitation
- id (Primary Key)
- family_id (Foreign Key → Family)
- email
- token (unique)
- invited_by (Foreign Key → User)
- status (choices: 'pending', 'accepted', 'expired')
- created_at
- expires_at

---

### Trip Core

#### Trip
- id (Primary Key)
- family_id (Foreign Key → Family)
- name (e.g., "Hawaii 2025")
- destination_name (e.g., "Maui")
- start_date
- end_date
- status (choices: 'planning', 'active', 'completed')
- created_by (Foreign Key → User)
- created_at
- updated_at

#### Resort
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- name
- website_url
- address_line1
- address_line2
- city
- state
- zip_code
- country
- latitude (for future distance calculations)
- longitude (for future distance calculations)
- general_notes (TextField)

---

### Notes System

#### NoteCategory
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- name (e.g., "Transportation", "Food Restrictions", "Emergency Contacts")
- color_code (hex color for UI organization)
- order (for sorting)

#### Note
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- category_id (Foreign Key → NoteCategory, nullable)
- title
- content (TextField)
- created_by (Foreign Key → User)
- created_at
- updated_at
- is_pinned (boolean - for important notes)

---

### Activities & Itinerary

#### Activity
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- name
- description (TextField)
- website_url
- address_line1
- address_line2
- city
- state
- zip_code
- latitude
- longitude
- distance_from_resort (decimal, can be manually entered initially)
- estimated_cost (decimal, nullable)
- estimated_duration (integer, minutes)
- pre_trip_priority (integer - ranking before trip)
- post_trip_rating (integer 1-5, nullable - after trip)
- post_trip_notes (TextField, nullable)
- is_favorite (boolean - flag for "would do again")
- created_by (Foreign Key → User)
- created_at
- updated_at

#### DailyItinerary
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- activity_id (Foreign Key → Activity, nullable - could be general event)
- date
- time_start (nullable)
- time_end (nullable)
- title (for non-activity events like "Check-in", "Breakfast")
- notes (TextField, nullable)
- order (for sorting multiple items on same day)

---

### Packing & Budget

#### PackingCategory
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- name (e.g., "Clothing", "Electronics", "Toiletries")
- order

#### PackingItem
- id (Primary Key)
- category_id (Foreign Key → PackingCategory)
- item_name
- quantity (integer, default 1)
- is_packed (boolean)
- assigned_to (Foreign Key → User, nullable - who's responsible for packing it)
- notes (nullable)
- order

#### BudgetCategory
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- name (e.g., "Lodging", "Food", "Activities", "Transportation")
- color_code

#### BudgetItem
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- category_id (Foreign Key → BudgetCategory)
- description
- estimated_amount (decimal)
- actual_amount (decimal, nullable)
- paid_by (Foreign Key → User, nullable)
- payment_date (nullable)
- notes (TextField, nullable)

---

### Memories & Media

#### TripPhoto
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- activity_id (Foreign Key → Activity, nullable)
- daily_itinerary_id (Foreign Key → DailyItinerary, nullable)
- image (ImageField)
- caption (TextField, nullable)
- taken_date (nullable)
- uploaded_by (Foreign Key → User)
- uploaded_at

#### DailyJournal
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- date
- content (TextField)
- weather (nullable, e.g., "Sunny, 78°F")
- mood_rating (integer 1-5, nullable)
- created_by (Foreign Key → User)
- created_at
- updated_at

---

### Sharing & Permissions

#### TripShare
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- shared_with_user (Foreign Key → User, nullable - if sharing with specific user)
- shared_with_family (Foreign Key → Family, nullable - if sharing with another family)
- permission_level (choices: 'view', 'comment', 'edit')
- shared_by (Foreign Key → User)
- created_at

#### Comment
- id (Primary Key)
- trip_id (Foreign Key → Trip)
- activity_id (Foreign Key → Activity, nullable)
- note_id (Foreign Key → Note, nullable)
- content (TextField)
- created_by (Foreign Key → User)
- created_at
- updated_at

---

## Detailed Implementation Plan

**Progress Tracker:**
- ✅ Phase 1: Foundation - COMPLETED (2025-10-07)
- ✅ Phase 2: Core Trip Management - COMPLETED (2025-10-07)
- ✅ Phase 3: Notes System - COMPLETED (2025-10-07)
- ⏳ Phase 4: Activities - Pending
- ⏳ Phase 5: Itinerary - Pending
- ⏳ Phase 6: Packing & Budget - Pending
- ⏳ Phase 7-10: Advanced Features - Pending

---

### Phase 1: Foundation (Week 1) ✅ COMPLETED
1. Set up Django project with Postgres
2. Configure Django User authentication
3. Create Family and FamilyMember models
4. Build simple family creation/invitation system
5. Basic templates and navigation structure

**Deliverable**: Users can register, create a family, invite members

**✅ What Was Built:**
- Family, FamilyMember, FamilyInvitation models with UUIDs
- Role-based permissions (owner/admin/member)
- Family creation, editing, member management
- Email-based invitations with 7-day expiration
- Responsive templates with HaleWay color scheme
- Structured logging throughout
- Django admin interface for families

---

### Phase 2: Core Trip Management (Week 2) ✅ COMPLETED
1. Create Trip and Resort models
2. Build trip creation form (name, dates, destination)
3. Resort details form with address fields
4. Trip dashboard showing all family trips
5. Trip detail page with resort info

**Deliverable**: Users can create trips with resort details

**✅ What Was Built:**
- Trip and Resort models with full address fields
- Trip status tracking (planning/active/completed)
- Trip list views (all trips, family-specific)
- Trip creation with optional resort info
- Resort detail editing with address and notes
- Trip permissions (creator + admins can edit)
- Duration calculation and date validation
- Responsive trip cards with status badges
- Integration with family management

---

### Phase 3: Notes System (Week 2-3) ✅ COMPLETED
1. Create NoteCategory and Note models
2. Build category management (add/edit/delete categories)
3. Note creation with category assignment
4. Search functionality across notes (full-text search)
5. Note pinning feature

**Deliverable**: Categorized, searchable notes system

**✅ What Was Built:**
- NoteCategory and Note models with PostgreSQL full-text search
- Color-coded category system with custom ordering
- Full CRUD views for notes and categories
- PostgreSQL full-text search on note title and content
- Search filtering by category and pinned status
- Note pinning feature for important notes
- Role-based permissions (all members create, creators/admins edit)
- Admin interface with inline note editing
- Integration with trip management
- Structured logging for all note operations

**🎨 Bonus Features Added:**
- PWA (Progressive Web App) support with manifest.json
- Multiple icon sizes generated (72x72 to 512x512)
- Favicon and Apple Touch Icon
- Open Graph and Twitter Card meta tags for social sharing
- Share image configuration using default-share.png

---

### Phase 4: Activities (Week 3-4)
1. Create Activity model
2. Activity creation form (all fields except distance calculation)
3. Manual distance entry field
4. Pre-trip priority drag-and-drop ordering
5. Activity list view with sorting options

**Deliverable**: Add and prioritize activities

---

### Phase 5: Itinerary (Week 4)
1. Create DailyItinerary model
2. Calendar view for trip dates
3. Drag activities onto specific days/times
4. Day-by-day itinerary view
5. Quick add for non-activity events

**Deliverable**: Daily schedule planning

---

### Phase 6: Packing & Budget (Week 5)
1. Create packing list models
2. Packing list UI with checkboxes
3. Create budget models
4. Budget tracking interface
5. Budget summary/totals

**Deliverable**: Packing and budget management

---

### Phase 7: Post-Trip Features (Week 5-6)
1. Post-trip rating system for activities
2. Favorite flagging
3. Post-trip notes on activities
4. Trip photo upload (to activities or days)
5. Daily journal entries

**Deliverable**: Document and rate trip experiences

---

### Phase 8: Search & Memories (Week 6)
1. Global search across past trips
2. "Top Activities" view (favorites, high ratings)
3. Filter by resort, destination, dates
4. Memory/highlight reel view
5. Export trip summary (bonus)

**Deliverable**: Find and revisit favorite experiences

---

### Phase 9: Sharing & Polish (Week 7)
1. Trip sharing with other families (view-only initially)
2. Comments on activities/notes
3. Permission system refinement
4. UI polish and responsive design
5. Weather widget integration (optional API)

**Deliverable**: Share trips with friends/extended family

---

### Phase 10: Advanced Features (Future)
1. Automatic distance calculation via Google Maps API
2. Real-time collaboration
3. Mobile app considerations
4. Email notifications for shared trips
5. Trip templates (reuse structure for similar trips)

---

## Key Django App Structure

```
family_vacation_planner/
├── accounts/          # User auth, profiles
├── families/          # Family management
├── trips/             # Trip, Resort models
├── notes/             # Notes, categories
├── activities/        # Activities, ratings
├── itinerary/         # Daily planning
├── packing/           # Packing lists
├── budget/            # Budget tracking
├── media/             # Photos, journals
└── sharing/           # Permissions, comments
```

---

## Indexes & Performance Considerations

**Critical Indexes:**
- `Trip.family_id` + `Trip.status`
- `Activity.trip_id` + `Activity.pre_trip_priority`
- `Activity.trip_id` + `Activity.post_trip_rating`
- `Note.trip_id` + `Note.category_id`
- Full-text search index on `Note.content` and `Note.title`
- `DailyItinerary.trip_id` + `DailyItinerary.date`

---

## Search Strategy

### Searchable Notes and Activities
- Use Django's `search` fields with Postgres full-text search
- Create a combined search view that queries: Notes, Activities, Trip names, Resort names
- Display results with: category, trip name, date range, relevant snippet

### Top Activities Future Search
- Query: `Activity.objects.filter(is_favorite=True, post_trip_rating__gte=4)`
- Include related Trip, Resort data
- Allow filters by destination, date range, activity type

---

## MVP Features (Quick Launch)

**Essential for v1:**
- User authentication & family creation
- Trip creation with resort details
- Activity list with manual distance entry
- Basic note system
- Pre-trip priority ordering

**Can defer:**
- Automatic distance calculation (use Google Maps API later)
- Multi-category notes system (start with single text field)
- Sharing/family permissions
- Post-trip ratings and search
- Budget tracking
- Packing lists

---

## Notes
- Start simple and iterate - get core trip planning working first
- Each phase builds naturally on the previous one
- App is usable after Phase 4
- Focus on family collaboration and memory-keeping
- Keep UI clean and mobile-friendly from the start