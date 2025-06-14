from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from . import views
from credits import views as credits_views
from .sitemaps import StaticViewSitemap, TrackgramsSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'trackgrams': TrackgramsSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('pricing/', credits_views.pricing_view, name='pricing'),
    path('pricing/create-payment-intent/', credits_views.create_payment_intent, name='pricing_payment_intent'),
    path('pricing/success/', credits_views.payment_success, name='pricing_success'),
    path('pricing/webhook/', credits_views.stripe_webhook, name='pricing_webhook'),
    path('accounts/', include('allauth.urls')),
    path('trackgrams/', include('trackgrams.urls')),
    path('credits/', include('credits.urls', namespace='credits')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)