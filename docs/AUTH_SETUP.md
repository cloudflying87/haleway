# Authentication Setup Guide

## Overview

Your haleway project includes a complete authentication system with:
- **Custom User Model** (can't be added later!)
- **Login Method**: Both
- **Auth Type**: Hybrid (Web + API)
- **Two-Factor Authentication**: Enabled ✓
- **Email Verification**: Disabled
- **Password Strength**: Django validators enabled

## Quick Start

### 1. Run Migrations (Creates User Table)

```bash
# Create migration files for your custom User model
python manage.py makemigrations accounts

# Apply all migrations
python manage.py migrate
```

This creates the `users` table in your database.

### 2. Create Your First Superuser

```bash
python manage.py createsuperuser
```

**What you'll be asked:**
- **Username**: Your login identifier
- **Email**: Your email address
- **Password**: Must meet these requirements:
  - Minimum 8 characters
  - Can't be too similar to your username
  - Can't be a common password (like "password123")
  - Can't be entirely numeric

**Example:**
```
Username: admin
Email address: admin@example.com
Password: ********
Password (again): ********
Superuser created successfully!
```

**💡 Password Tips:**
- Use a passphrase: `BlueSky-Mountain-42!`
- Mix letters, numbers, symbols
- Store in password manager (1Password, LastPass, Bitwarden)

### 3. Test Your Setup

**Start the dev server:**
```bash
python manage.py runserver
```

**Web Login** (if using web/hybrid):
- Go to: http://localhost:8000/accounts/login/
- Login with your superuser credentials
- Access admin: http://localhost:8000/admin/

**API Login** (if using api/hybrid):
```bash
# Get JWT tokens
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Use token in subsequent requests
curl http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Custom User Model Details

### Location: `apps/accounts/models.py`

Your custom User model extends Django's `AbstractUser` and adds:

```python
class User(AbstractUser):
    # Login field
    USERNAME_FIELD = 'both'  # Users log in with username

    # Additional fields
    email = models.EmailField(unique=True)  # Always unique
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    email_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Adding Custom Fields

Want to add more fields? Edit `apps/accounts/models.py`:

```python
class User(AbstractUser):
    # ... existing fields ...

    # Your custom fields
    date_of_birth = models.DateField(null=True, blank=True)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
```

**Then create and run migration:**
```bash
python manage.py makemigrations accounts -m "Add custom user fields"
python manage.py migrate
```

## Available Endpoints

### Web Endpoints (Browser)

- **Login**: `/accounts/login/`
- **Logout**: `/accounts/logout/`
- **Register**: `/accounts/register/`
- **Profile**: `/accounts/profile/`
- **Password Reset**: `/accounts/password-reset/`
- **Password Change**: `/accounts/password-change/`

### API Endpoints (JSON)

- **Register**: `POST /api/auth/register/`
- **Get Token**: `POST /api/auth/token/`
- **Refresh Token**: `POST /api/auth/token/refresh/`
- **Current User**: `GET /api/auth/me/`

## Password Requirements Explained

Django includes these validators by default (configured in `settings/base.py`):

### 1. UserAttributeSimilarityValidator
❌ **Bad**: If username is "john", password can't be "john123"
✅ **Good**: Password is different from username/email

### 2. MinimumLengthValidator
❌ **Bad**: "pass123" (too short)
✅ **Good**: At least 8 characters

### 3. CommonPasswordValidator
❌ **Bad**: "password", "123456", "qwerty"
✅ **Good**: Not in list of 20,000 common passwords

### 4. NumericPasswordValidator
❌ **Bad**: "12345678" (all numbers)
✅ **Good**: Mix of letters and numbers

**Adjust in `settings/base.py` if needed:**
```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Require 12 characters instead of 8
    },
    # ... other validators
]
```

## Creating Regular Users

### Via Web Interface
Users can self-register at `/accounts/register/`

### Via Django Shell
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create regular user
user = User.objects.create_user(
    username='johndoe',
    email='johndoe@example.com',
    password='SecurePass123!',
    first_name='John',
    last_name='Doe'
)

# Create staff user (can access admin)
staff = User.objects.create_user(
    username='staff',
    password='SecurePass123!',
    is_staff=True  # Can access admin
)
```

### Via Management Command (Bulk Import)
```bash
# Create: apps/accounts/management/commands/create_users.py
python manage.py create_users users.csv
```

## Authentication in Views

### Web Views (Function-Based)
```python
from django.contrib.auth.decorators import login_required

@login_required  # Redirects to /accounts/login/ if not logged in
def my_view(request):
    user = request.user  # Current logged-in user
    return render(request, 'my_template.html', {'user': user})
```

### Web Views (Class-Based)
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class MyView(LoginRequiredMixin, TemplateView):
    template_name = 'my_template.html'
    login_url = '/accounts/login/'  # Optional: custom login URL
```

### API Views
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Requires JWT token
def my_api_view(request):
    user = request.user  # User from JWT token
    return Response({'message': f'Hello, {user.email}'})
```

## Testing Authentication

### Test User Creation
```python
# tests/test_auth.py
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()

class AuthTestCase(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('TestPass123!'))
```

### Test Login
```python
def test_login(self):
    # Create user
    user = User.objects.create_user(
        username='testuser',
        password='TestPass123!'
    )

    # Test login
    logged_in = self.client.login(
        username='testuser',
        password='TestPass123!'
    )
    self.assertTrue(logged_in)
```

## Troubleshooting

### "No such table: users"
**Solution**: Run migrations
```bash
python manage.py migrate
```

### "Superuser must have is_superuser=True"
**Solution**: Use `create_superuser()` not `create_user()`
```python
User.objects.create_superuser(...)  # ✓ Correct
```

### "Password doesn't meet requirements"
**Solution**: Make password stronger (8+ chars, not common, not all numbers)

### "Email already exists" (when using email login)
**Solution**: Each email must be unique. Use different email or delete existing user:
```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(email='duplicate@example.com').delete()
```

### JWT Token Invalid/Expired
**Solution**: Get new token or use refresh token
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## Security Best Practices

✅ **DO**:
- Store .env file securely (already gitignored)
- Use strong SECRET_KEY (automatically generated)
- Enable HTTPS in production
- Use environment-specific settings (development.py vs production.py)
- Rotate JWT tokens regularly
- Log authentication attempts

❌ **DON'T**:
- Commit .env to git (already prevented)
- Use DEBUG=True in production
- Store passwords in plain text
- Share SECRET_KEY publicly
- Use default Django SECRET_KEY

## Production Checklist

Before deploying:

- [ ] Set `DEBUG=False` in .env
- [ ] Configure proper `ALLOWED_HOSTS` in .env
- [ ] Set up SMTP for email (password reset)
- [ ] Enable HTTPS
- [ ] Configure CORS for your frontend domain
- [ ] Set up proper logging/monitoring
- [ ] Test password reset flow
- [ ] Test JWT token expiration
- [ ] Configure 2FA (TOTP apps: Google Authenticator, Authy)

## Additional Resources

- [Django Authentication Docs](https://docs.djangoproject.com/en/5.0/topics/auth/)
- [DRF Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

*Generated for haleway on 2025-10-07*
*Login method: both | Auth type: hybrid*
