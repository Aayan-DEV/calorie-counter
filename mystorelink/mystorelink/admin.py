from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['stripe_customer_id']
    readonly_fields = ['created_at', 'updated_at']

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = BaseUserAdmin.list_display + ('get_stripe_customer_id', 'get_profile_created_at')
    
    def get_stripe_customer_id(self, obj):
        try:
            return obj.profile.stripe_customer_id or 'Not set'
        except UserProfile.DoesNotExist:
            return 'No profile'
    get_stripe_customer_id.short_description = 'Stripe Customer ID'
    
    def get_profile_created_at(self, obj):
        try:
            return obj.profile.created_at
        except UserProfile.DoesNotExist:
            return 'No profile'
    get_profile_created_at.short_description = 'Profile Created'

# Register UserProfile separately for detailed management
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'stripe_customer_id', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'stripe_customer_id']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Stripe Information', {
            'fields': ('stripe_customer_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)