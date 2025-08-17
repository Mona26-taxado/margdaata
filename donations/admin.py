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

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'mobile', 'reference_name', 'approved', 'created_at')
    list_filter = ('approved', 'gender', 'department', 'created_at')
    search_fields = ('name', 'email', 'mobile', 'reference_name')
    readonly_fields = ('md_code', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'mobile', 'gender', 'dob', 'aadhar', 'md_code')
        }),
        ('Address Information', {
            'fields': ('home_address', 'home_state', 'home_district', 'posting_state', 'posting_district')
        }),
        ('Professional Information', {
            'fields': ('department', 'post', 'disease', 'blood_group')
        }),
        ('Reference Information', {
            'fields': ('reference_name',)
        }),
        ('Nominee Information', {
            'fields': ('first_nominee_name', 'first_nominee_relation', 'first_nominee_mobile')
        }),
        ('Status', {
            'fields': ('approved', 'created_at')
        }),
    )




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

