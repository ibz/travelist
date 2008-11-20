import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'backpackedit'
DATABASE_USER = 'bit'
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = '5432'

FIXTURE_DIRS = ("fixtures",)

LOGIN_URL = "/account/login/"
LOGOUT_URL = "/account/logout/"

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'
USE_I18N = True

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "media")
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin-media/'

SECRET_KEY = '@2s!oe3(g2w(sifra4t+=!whk79-b-3p8gr4o!fw#a_x4deht3'

SERVER_EMAIL = "contact@backpacked.it"
CUSTOMER_EMAIL = "contact@backpacked.it"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "contact@backpacked.it"
EMAIL_HOST_PASSWORD = "39L423"
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = "[backpacked.it] "

APPEND_SLASH = True

AUTH_PROFILE_MODULE = 'backpacked.UserProfile'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source')

TEMPLATE_CONTEXT_PROCESSORS = (
'django.core.context_processors.auth',
'django.core.context_processors.media')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = [
    os.path.join(os.path.dirname(__file__), "templates")
]

INSTALLED_APPS = (
    'backpacked',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
)

GOOGLE_MAPS_API_KEY = "ABQIAAAAq_mjC_qAMFZ-7Y07h8CbfxRKR2kFp3iqjCq4a6HN9rHMOG-QDRRCAx73IYXNGFNtbDRPrqsSVloaWQ"

DATE_FORMAT_SHORT_JS = "yy-mm-dd"
DATE_FORMAT_LONG_JS = "M. d, yy"

DATE_FORMAT_SHORT_PY = "%Y-%m-%d"
TIME_FORMAT_SHORT_PY = "%H:%M"
TIME_FORMAT_LONG_PY = TIME_FORMAT_SHORT_PY + ":%S"
DATE_TIME_FORMAT_SHORT_PY = "%s %s" % (DATE_FORMAT_SHORT_PY, TIME_FORMAT_SHORT_PY)

execfile(os.path.join(os.path.dirname(__file__), "settings_local.py"))

