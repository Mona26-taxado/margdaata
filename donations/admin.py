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

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()  # Get custom user model

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "message", "target_type", "specific_user", "created_at")  # Removed `is_active`
    list_filter = ("target_type", "created_at")  # Filtering by valid fields
    search_fields = ("title", "message", "specific_user__email")  # Searching by user email if specific

    def specific_user_email(self, obj):
        return obj.specific_user.email if obj.specific_user else "All Users"

    specific_user_email.short_description = "Specific User Email"

