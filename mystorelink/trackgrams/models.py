from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

def get_supabase_storage():
    from mystorelink.supabase_storage import SupabaseStorage
    return SupabaseStorage(bucket_name='photos')

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='photos/%Y/%m/%d/',
        storage=get_supabase_storage  # Use callable function
    )
    supabase_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Photo'
        verbose_name_plural = 'Photos'
    
    def __str__(self):
        return f"Photo by {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

class FoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    food_name = models.CharField(max_length=200)
    grams = models.IntegerField()  # Add this field
    calories = models.IntegerField()  # Rename from calories_per_unit
    protein = models.IntegerField(default=0)  # Add this field
    carbs = models.IntegerField(default=0)    # Add this field
    fat = models.IntegerField(default=0)      # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Food Entry'
        verbose_name_plural = 'Food Entries'
    
    def __str__(self):
        return f"{self.food_name} - {self.grams}g ({self.calories} cal)"
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_calorie_goal = models.IntegerField(default=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"