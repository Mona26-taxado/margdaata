from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Customer

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'role', 'is_active', 'is_approved')  # ✅ Removed 'username'
    ordering = ('email',)  # ✅ Use email for ordering
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role', 'is_active', 'is_approved')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'is_approved')}
        ),
    )
    search_fields = ('email',)  # ✅ Remove 'username'

admin.site.register(CustomUser, CustomUserAdmin)




# Register your models here.

from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('message',)
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected notifications as active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected notifications as inactive"
