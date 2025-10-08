"""
Django admin configuration for families app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Family, FamilyMember, FamilyInvitation


class FamilyMemberInline(admin.TabularInline):
    """Inline admin for family members."""
    model = FamilyMember
    extra = 0
    readonly_fields = ['joined_at']
    fields = ['user', 'role', 'joined_at']


class FamilyInvitationInline(admin.TabularInline):
    """Inline admin for family invitations."""
    model = FamilyInvitation
    extra = 0
    readonly_fields = ['created_at', 'expires_at', 'token']
    fields = ['email', 'status', 'invited_by', 'created_at', 'expires_at']


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    """Admin interface for Family model."""
    list_display = ['name', 'member_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [FamilyMemberInline, FamilyInvitationInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    """Admin interface for FamilyMember model."""
    list_display = ['user', 'family', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'user__email', 'family__name']
    readonly_fields = ['id', 'joined_at']

    fieldsets = (
        ('Member Information', {
            'fields': ('family', 'user', 'role')
        }),
        ('Metadata', {
            'fields': ('id', 'joined_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FamilyInvitation)
class FamilyInvitationAdmin(admin.ModelAdmin):
    """Admin interface for FamilyInvitation model."""
    list_display = ['email', 'family', 'status', 'invited_by', 'created_at', 'expires_at', 'status_badge']
    list_filter = ['status', 'created_at']
    search_fields = ['email', 'family__name']
    readonly_fields = ['id', 'token', 'created_at', 'expires_at']

    fieldsets = (
        ('Invitation Details', {
            'fields': ('family', 'email', 'status', 'invited_by')
        }),
        ('Token & Expiration', {
            'fields': ('token', 'created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display a colored status badge."""
        colors = {
            'pending': '#ffc107',
            'accepted': '#28a745',
            'expired': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
