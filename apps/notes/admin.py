"""
Django admin configuration for notes app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import NoteCategory, Note


class NoteInline(admin.TabularInline):
    """Inline admin for notes within a category."""
    model = Note
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['title', 'is_pinned', 'created_by', 'created_at']
    show_change_link = True


@admin.register(NoteCategory)
class NoteCategoryAdmin(admin.ModelAdmin):
    """Admin interface for NoteCategory model."""
    list_display = ['name', 'trip', 'color_badge', 'order', 'note_count']
    list_filter = ['trip']
    search_fields = ['name', 'trip__name']
    readonly_fields = ['id']
    inlines = [NoteInline]

    fieldsets = (
        ('Category Information', {
            'fields': ('trip', 'name', 'color_code', 'order')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def color_badge(self, obj):
        """Display a colored badge for the category."""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            obj.color_code,
            obj.get_color_code_display()
        )
    color_badge.short_description = 'Color'

    def note_count(self, obj):
        """Display the number of notes in this category."""
        return obj.notes.count()
    note_count.short_description = 'Notes'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin interface for Note model."""
    list_display = ['title', 'trip', 'category', 'is_pinned', 'created_by', 'created_at', 'updated_at']
    list_filter = ['is_pinned', 'category', 'created_at']
    search_fields = ['title', 'content', 'trip__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'search_vector']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Note Information', {
            'fields': ('trip', 'category', 'title', 'content', 'is_pinned')
        }),
        ('Creator & Timestamps', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
        ('Search', {
            'fields': ('search_vector',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('trip', 'category', 'created_by')
