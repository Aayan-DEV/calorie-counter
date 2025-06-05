from django.urls import path
from . import views

app_name = 'trackgrams'

urlpatterns = [
    path('', views.camera_capture, name='camera_capture'),
    path('save-photo/', views.save_photo, name='save_photo'),
    path('analyze-nutrition/', views.analyze_nutrition, name='analyze_nutrition'),
    path('add-food-entry/', views.add_food_entry, name='add_food_entry'),
    path('delete-food-entry/<int:entry_id>/', views.delete_food_entry, name='delete_food_entry'),
    path('get-food-entries/', views.get_food_entries, name='get_food_entries'),
]