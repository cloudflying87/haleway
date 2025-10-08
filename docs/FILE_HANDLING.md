# File Handling Guide

## Overview

This guide covers best practices for handling file uploads in haleway, including user uploads, bulk data imports, and security considerations.

## Django Media Files Setup

Your project is already configured with:
- `MEDIA_ROOT`: Where uploaded files are stored
- `MEDIA_URL`: URL prefix for serving media files
- Docker volume mounting for persistent storage
- `.gitignore` excludes `media/` directory

## User-Uploaded Files (Images, Documents, PDFs)

### 1. Model Setup

```python
# apps/core/models.py
from django.db import models
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    """Example model for file uploads."""
    title = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    # File field with validation
    file = models.FileField(
        upload_to='documents/%Y/%m/',  # Organized by year/month
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])
        ],
        help_text="Allowed: PDF, DOC, DOCX (max 10MB)"
    )

    # Image field (automatically validates image formats)
    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(help_text="File size in bytes")

    def save(self, *args, **kwargs):
        # Store file size on save
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-uploaded_at']

class UserProfile(models.Model):
    """Example for user avatar uploads."""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Profile picture"
    )
```

### 2. Form Handling

```python
# apps/core/forms.py
from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'thumbnail']
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'}),
            'thumbnail': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if file:
            # Validate file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB")

            # Validate content type
            allowed_types = ['application/pdf', 'application/msword',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if file.content_type not in allowed_types:
                raise forms.ValidationError("Invalid file type")

        return file
```

### 3. View Implementation

```python
# apps/core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DocumentUploadForm

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            return redirect('document_list')
    else:
        form = DocumentUploadForm()

    return render(request, 'core/upload.html', {'form': form})
```

### 4. Template (Mobile-First)

```html
<!-- templates/core/upload.html -->
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container">
    <div class="card">
        <div class="card-header">
            <h2>Upload Document</h2>
        </div>
        <div class="card-body">
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}

                <div class="form-group">
                    <label for="id_title" class="form-label">
                        Title <span class="required">*</span>
                    </label>
                    {{ form.title }}
                    {% if form.title.errors %}
                        <div class="form-errors">{{ form.title.errors }}</div>
                    {% endif %}
                </div>

                <div class="form-group">
                    <label for="id_file" class="form-label">
                        Document <span class="required">*</span>
                    </label>
                    {{ form.file }}
                    <div class="form-help">Allowed: PDF, DOC, DOCX (max 10MB)</div>
                    {% if form.file.errors %}
                        <div class="form-errors">{{ form.file.errors }}</div>
                    {% endif %}
                </div>

                <div class="btn-group">
                    <button type="submit" class="btn btn-primary">Upload</button>
                    <a href="{% url 'document_list' %}" class="btn btn-outline">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

## Bulk Data Import (CSV, Excel)

### CSV Import Example

```python
# apps/core/management/commands/import_data.py
import csv
from django.core.management.base import BaseCommand
from apps.core.models import YourModel

class Command(BaseCommand):
    help = 'Import data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)

            created_count = 0
            for row in reader:
                obj, created = YourModel.objects.get_or_create(
                    field1=row['column1'],
                    defaults={
                        'field2': row['column2'],
                        'field3': row['column3'],
                    }
                )
                if created:
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {created_count} records')
            )

# Usage: python manage.py import_data data.csv
```

### Excel Import (with pandas)

```python
# Add to requirements/base.txt: pandas>=2.0.0 openpyxl>=3.1.0

import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Import data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str)

    def handle(self, *args, **options):
        df = pd.read_excel(options['excel_file'])

        for index, row in df.iterrows():
            YourModel.objects.create(
                field1=row['Column1'],
                field2=row['Column2'],
            )

        self.stdout.write(
            self.style.SUCCESS(f'Imported {len(df)} records')
        )
```

## Security Best Practices

### 1. File Validation

```python
# apps/core/validators.py
from django.core.exceptions import ValidationError
import magic  # pip install python-magic

def validate_file_type(file):
    """Validate file type using magic numbers (not just extension)."""
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png']

    # Read first 2048 bytes to detect file type
    file_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)  # Reset file pointer

    if file_type not in allowed_types:
        raise ValidationError(f'Unsupported file type: {file_type}')

def validate_image_dimensions(image):
    """Ensure image meets size requirements."""
    if image.width > 4000 or image.height > 4000:
        raise ValidationError('Image dimensions too large (max 4000x4000)')

    if image.width < 100 or image.height < 100:
        raise ValidationError('Image dimensions too small (min 100x100)')
```

### 2. Virus Scanning (Production)

```python
# For production environments, consider ClamAV integration
# pip install clamd

import clamd

def scan_file_for_viruses(file):
    """Scan uploaded file for viruses."""
    cd = clamd.ClamdUnixSocket()

    # Scan file
    result = cd.instream(file)

    if result['stream'][0] == 'FOUND':
        raise ValidationError('File failed virus scan')
```

### 3. Secure File Storage

```python
# config/settings/base.py

# Generate random filenames to prevent directory traversal
import os
import uuid

def user_directory_path(instance, filename):
    """Generate secure upload path."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('user_{0}'.format(instance.user.id), filename)

# Use in model:
# file = models.FileField(upload_to=user_directory_path)
```

### 4. Serving Files Securely

```python
# apps/core/views.py
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
import os

@login_required
def serve_protected_file(request, document_id):
    """Serve files only to authorized users."""
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        raise Http404

    # Check permissions
    if document.uploaded_by != request.user and not request.user.is_staff:
        raise Http404

    # Serve file
    file_path = document.file.path
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )

    raise Http404
```

## Image Processing

### Thumbnail Generation

```python
# pip install Pillow (already in requirements)

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def create_thumbnail(image_field, size=(300, 300)):
    """Create thumbnail from uploaded image."""
    img = Image.open(image_field)

    # Convert RGBA to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    # Create thumbnail
    img.thumbnail(size, Image.Resampling.LANCZOS)

    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)

    return InMemoryUploadedFile(
        output, 'ImageField',
        f"thumb_{image_field.name}",
        'image/jpeg',
        output.getbuffer().nbytes,
        None
    )

# Use in model save():
# if self.image and not self.thumbnail:
#     self.thumbnail = create_thumbnail(self.image)
```

## Cloud Storage (AWS S3)

### Setup for Production

```python
# pip install boto3 django-storages

# config/settings/production.py

INSTALLED_APPS += ['storages']

# AWS S3 Settings
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Static/Media file storage
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Security
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
```

## Testing File Uploads

```python
# tests/test_uploads.py
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.models import Document

class FileUploadTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'password')
        self.client.login(username='test', password='password')

    def test_upload_valid_file(self):
        # Create fake file
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            file_content,
            content_type="application/pdf"
        )

        response = self.client.post('/upload/', {
            'title': 'Test Document',
            'file': uploaded_file
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Document.objects.count(), 1)

    def test_upload_oversized_file(self):
        # Create file larger than 10MB
        large_file = SimpleUploadedFile(
            "large.pdf",
            b'x' * (11 * 1024 * 1024),  # 11MB
            content_type="application/pdf"
        )

        response = self.client.post('/upload/', {
            'title': 'Large File',
            'file': large_file
        })

        self.assertFormError(response, 'form', 'file', 'File size must be under 10MB')
```

## Domain-Specific Considerations

**For travel applications:**


- Consider what types of files users will upload
- Plan for file retention and cleanup policies
- Determine access control requirements
- Consider backup and disaster recovery
- Plan for file format conversions if needed


## Checklist

- [ ] Models have appropriate FileField/ImageField validators
- [ ] Forms validate file size and type
- [ ] Views check user permissions before serving files
- [ ] Files stored with secure, random filenames
- [ ] Media files excluded from git (.gitignore)
- [ ] Docker volumes configured for media persistence
- [ ] Thumbnails generated for images (if needed)
- [ ] Consider virus scanning for production
- [ ] Plan for cloud storage (S3) if scaling

## Additional Resources

- [Django File Uploads](https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/)
- [Handling User Uploads](https://docs.djangoproject.com/en/5.0/ref/models/fields/#filefield)
- [django-storages Documentation](https://django-storages.readthedocs.io/)

---

*Generated for haleway on 2025-10-07*
