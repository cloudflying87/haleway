"""
Forms for note and category management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import NoteCategory, Note


class NoteCategoryForm(forms.ModelForm):
    """Form for creating and editing note categories."""

    class Meta:
        model = NoteCategory
        fields = ['name', 'color_code', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Transportation, Food, Emergency Contacts',
                'required': True
            }),
            'color_code': forms.Select(attrs={
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            })
        }
        labels = {
            'name': _('Category Name'),
            'color_code': _('Color'),
            'order': _('Display Order')
        }
        help_texts = {
            'name': _('Choose a descriptive name for this category.'),
            'color_code': _('Select a color to help organize your notes.'),
            'order': _('Lower numbers appear first (0 = first).')
        }

    def __init__(self, *args, trip=None, **kwargs):
        """Initialize form with trip."""
        super().__init__(*args, **kwargs)
        self.trip = trip

    def clean_name(self):
        """Validate category name is unique for this trip."""
        name = self.cleaned_data.get('name')
        if not name or len(name.strip()) < 2:
            raise ValidationError(_('Category name must be at least 2 characters long.'))

        # Check uniqueness within the trip (excluding current instance if editing)
        if self.trip:
            qs = NoteCategory.objects.filter(trip=self.trip, name=name.strip())
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('A category with this name already exists for this trip.'))

        return name.strip()

    def save(self, commit=True):
        """Save the category with trip."""
        category = super().save(commit=False)
        if self.trip:
            category.trip = self.trip
        if commit:
            category.save()
        return category


class NoteForm(forms.ModelForm):
    """Form for creating and editing notes."""

    class Meta:
        model = Note
        fields = ['category', 'title', 'content', 'is_pinned']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Note title',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your note here...',
                'rows': 6,
                'required': True
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'category': _('Category'),
            'title': _('Title'),
            'content': _('Content'),
            'is_pinned': _('Pin this note')
        }
        help_texts = {
            'category': _('Optionally categorize this note.'),
            'title': _('A brief, descriptive title.'),
            'content': _('The full content of your note.'),
            'is_pinned': _('Pinned notes appear at the top of the list.')
        }

    def __init__(self, *args, trip=None, created_by=None, **kwargs):
        """Initialize form with trip and creator."""
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.created_by = created_by

        # Limit category choices to categories for this trip
        if trip:
            self.fields['category'].queryset = NoteCategory.objects.filter(trip=trip)
            self.fields['category'].empty_label = '-- No Category --'

    def clean_title(self):
        """Validate note title."""
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 2:
            raise ValidationError(_('Title must be at least 2 characters long.'))
        return title.strip()

    def clean_content(self):
        """Validate note content."""
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 1:
            raise ValidationError(_('Note content cannot be empty.'))
        return content.strip()

    def save(self, commit=True):
        """Save the note with trip and creator."""
        note = super().save(commit=False)
        if self.trip:
            note.trip = self.trip
        if self.created_by:
            note.created_by = self.created_by
        if commit:
            note.save()
        return note


class NoteSearchForm(forms.Form):
    """Form for searching notes."""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search notes...',
            'type': 'search'
        }),
        label=''
    )
    category = forms.ModelChoiceField(
        queryset=NoteCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Filter by category'),
        empty_label='-- All Categories --'
    )
    pinned_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('Pinned only')
    )

    def __init__(self, *args, trip=None, **kwargs):
        """Initialize form with trip for category filtering."""
        super().__init__(*args, **kwargs)
        if trip:
            self.fields['category'].queryset = NoteCategory.objects.filter(trip=trip)
