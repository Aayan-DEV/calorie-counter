from django.urls import path
from . import views

app_name = 'trackgrams'

urlpatterns = [
    path('', views.camera_capture, name='camera_capture'),
    path('save-photo/', views.save_photo, name='save_photo'),
    path('analyze-nutrition/', views.analyze_nutrition, name='analyze_nutrition'),  # New endpoint
]