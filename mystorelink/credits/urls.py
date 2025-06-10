from django.urls import path
from . import views

app_name = 'credits'

urlpatterns = [
    path('', views.pricing_view, name='pricing'),
    path('purchase/', views.pricing_view, name='purchase'),  # Add purchase URL
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('success/', views.payment_success, name='payment_success'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]   