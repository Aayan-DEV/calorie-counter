from django.contrib import admin
from .models import FoodEntry, UserProfile, Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['user', 'image', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('user', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    # ... existing code ...
    list_display = ['food_name', 'user', 'quantity', 'unit', 'calories_per_unit', 'total_calories', 'date_added']
    list_filter = ['unit', 'date_added', 'user']
    search_fields = ['food_name', 'user__username']
    readonly_fields = ['total_calories', 'created_at', 'updated_at']
    date_hierarchy = 'date_added'
    
    fieldsets = (
        ('Food Information', {
            'fields': ('food_name', 'quantity', 'unit', 'calories_per_unit')
        }),
        ('User & Date', {
            'fields': ('user', 'date_added')
        }),
        ('Calculated Fields', {
            'fields': ('total_calories',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # ... existing code ...
    list_display = ['user', 'daily_calorie_goal', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']