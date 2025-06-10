from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from credits import views as credits_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('pricing/', credits_views.pricing_view, name='pricing'),
    path('pricing/create-payment-intent/', credits_views.create_payment_intent, name='pricing_payment_intent'),
    path('pricing/success/', credits_views.payment_success, name='pricing_success'),  # Add this line
    path('pricing/webhook/', credits_views.stripe_webhook, name='pricing_webhook'),  # Add this line
    path('accounts/', include('allauth.urls')),
    path('trackgrams/', include('trackgrams.urls')),
    path('credits/', include('credits.urls', namespace='credits')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)