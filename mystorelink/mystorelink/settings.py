from pathlib import Path
from decouple import config
from dotenv import load_dotenv
load_dotenv(override=True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Add at the top with other imports
import os
import dj_database_url

# Update ALLOWED_HOSTS
ALLOWED_HOSTS = [
    ".railway.app", 
    ".ngrok-free.app", 
    ".mystorel.ink",
    "localhost",
    "127.0.0.1",
    "192.168.0.16"
]

# Add CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    "https://*.railway.app",
    "https://*.mystorel.ink",
    "https://mystorel.ink",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.0.16:8000"
]

# Database configuration using Supabase PostgreSQL
CONN_MAX_AGE = config('CONN_MAX_AGE', default=300, cast=int)
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL is not None:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_health_checks=True,
            conn_max_age=CONN_MAX_AGE,
        )
    }
else:
    raise ValueError("DATABASE_URL environment variable is required")

# Static files configuration for production
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Add WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Ensure WhiteNoise is in MIDDLEWARE (should already be there)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # This should be here
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Static files compression
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'django_extensions',
    'django.contrib.sitemaps',
    
    # Allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Your apps
    'mystorelink',
    'trackgrams',
    'credits',
]

ROOT_URLCONF = 'mystorelink.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mystorelink.context_processors.google_oauth_settings',  # Add this line
            ],
        },
    },
]

WSGI_APPLICATION = 'mystorelink.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Supabase Configuration
SUPABASE_URL = config('SUPABASE_URL')
SUPABASE_KEY = config('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY')
SUPABASE_STORAGE_BUCKET = 'photos'

# Django Allauth Configuration
SITE_ID = 1

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Updated Allauth settings (new syntax)
ACCOUNT_LOGIN_METHODS = {'email'}  # Replaces ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # Replaces ACCOUNT_EMAIL_REQUIRED and ACCOUNT_USERNAME_REQUIRED
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Set to 'mandatory' for production
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Google OAuth settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Skip the intermediate signup form
SOCIALACCOUNT_AUTO_SIGNUP = True

# Skip email verification for social accounts
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

# Automatically connect social accounts to existing users with same email
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# Add this to completely bypass the signup form
SOCIALACCOUNT_SIGNUP_FORM_CLASS = None
SOCIALACCOUNT_LOGIN_ON_GET = True

# Google OAuth credentials (add these to your .env file)
GOOGLE_OAUTH2_CLIENT_ID = config('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = config('GOOGLE_OAUTH2_CLIENT_SECRET')

# Media files (uploads)
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Nutrition API Configuration
NUTRITION_API_URL = 'https://calorie-counter-api-production.up.railway.app'

NUTRITION_API_KEY = config('NUTRITION_API_KEY')

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Update LOGIN_REDIRECT_URL to go to pricing page
LOGIN_REDIRECT_URL = '/pricing/'
LOGOUT_REDIRECT_URL = '/'

SITE_ID = 1
SITE_URL = 'https://mystorel.ink'