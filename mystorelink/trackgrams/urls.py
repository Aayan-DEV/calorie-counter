from django.urls import path
from . import views

app_name = 'trackgrams'

urlpatterns = [
    path('', views.camera_capture, name='camera_capture'),
    path('upload/', views.save_photo, name='save_photo'),
    path('analyze/', views.analyze_nutrition, name='analyze_nutrition'),
    path('analyze-barcode/', views.analyze_barcode, name='analyze_barcode'),  # New endpoint
    path('add-food-entry/', views.add_food_entry, name='add_food_entry'),
    path('delete-food-entry/', views.delete_food_entry, name='delete_food_entry'),
    path('get-food-entries/', views.get_food_entries, name='get_food_entries'),
]