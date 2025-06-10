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
    list_display = ['food_name', 'user', 'grams', 'calories', 'protein', 'carbs', 'fat', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['food_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Food Information', {
            'fields': ('food_name', 'grams')
        }),
        ('Nutrition Information', {
            'fields': ('calories', 'protein', 'carbs', 'fat')
        }),
        ('User Information', {
            'fields': ('user',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_calorie_goal', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']