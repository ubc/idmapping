"""
Django settings for idmap project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import datetime

from idm.plugins.manager import PluginManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'n#13^fukafihm1y0o2i7keukym_!t_rlc%++_%srcg1gf0bzn+')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'idm.apps.IdmConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'django_extensions',
    'corsheaders',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'idmap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'idmap.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/volatile/static/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'PAGE_SIZE': 10
}

CORS_ORIGIN_ALLOW_ALL = True

DEFAULT_VERSION = 'v0'

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': DEFAULT_VERSION,
    'api_path': '/api',
    'enabled_methods': [
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
    'api_key': '',
    'is_authenticated': True,
    'is_superuser': False,
    'permission_denied_handler': None,
    'resource_access_handler': None,
    # 'base_path': 'localhost:8080/docs',
    'info': {
        'contact': 'pan.luo@ubc.ca',
        'description': 'This is a sample Identity Detective server. ',
        'license': 'Apache 2.0',
        'licenseUrl': 'http://www.apache.org/licenses/LICENSE-2.0.html',
        # 'termsOfServiceUrl': 'http://helloreverb.com/terms/',
        'title': 'Identity Detective',
    },
    'doc_expansion': 'none',
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=7200),
}

HASH_SALT = os.environ.get('HASH_SALT')
EDX_SERVER = os.environ.get('EDX_SERVER', 'http://localhost:8000')
EDX_MAPPING_ENDPOINT = os.environ.get('EDX_MAPPING_ENDPOINT', '/api/third_party_auth/v0/providers/saml-ubc/users')
EDX_ACCESS_TOKEN = os.environ.get('EDX_ACCESS_TOKEN')

PLUGINS = [
    # 'idm.plugins.providers.RemoteIdProvider',
    'idm.plugins.providers.UserInfoProvider',
    'idm.plugins.providers.EdxUsernameProvider',
]

PluginManager.register(*PLUGINS)

PROVIDER = {}

for provider in PluginManager.get_all_providers():
    provider_name = type(provider).__name__
    PROVIDER[provider_name] = {}
    for key, default in provider.settings.iteritems():
        PROVIDER[provider_name][key] = os.environ.get(key, default)
