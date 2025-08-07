import os
from pathlib import Path
from custom_settings import *
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-u+ailrty27v)8bp%_pwzvw*0q_($$$t)d4usf*x#bjg1y^(49a'
DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'
DATABASES = {}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'


def get_first_redis_connection(redis_connections):
    if redis_connections:
        first_key = next(iter(redis_connections))
        return redis_connections[first_key]
    return None  

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
BROKER_PORT = get_first_redis_connection(REDIS_CONNECTIONS)
CELERY_BROKER_URL = f'redis://localhost:{BROKER_PORT}/0'  
CELERY_RESULT_BACKEND = f'redis://localhost:{BROKER_PORT}/0'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULE_FILENAME = os.path.join(BASE_DIR, 'celerybeat-schedule')
  
CELERY_BEAT_SCHEDULE = {
    'delete-old-messages': {
        'task': 'project.tasks.delete_old_messages',  
        # Start every hour *******************************************
        'schedule': crontab(minute=0),  
    },
    'update-knowledge-bases': {
        'task': 'project.tasks.update_knowledge_bases',  
        # Start every day at 01:00 AM
        'schedule': crontab(hour=1, minute=0), 
    },
    'update-chat-kb': {
        'task': 'project.tasks.update_chat_kb',  
        # Start every day at 01:20 AM
        'schedule': crontab(hour=1, minute=20), 
    },
}