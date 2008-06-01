SITE_NAME = "backpacked.it"
SITE_URL = "http://backpacked.it"

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'kashgar'
DATABASE_USER = 'kashgar'
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'
USE_I18N = True

MEDIA_ROOT = '/home/ionut/work/kashgar/media/'
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin-media/'

SECRET_KEY = '@2s!oe3(g2w(sifra4t+=!whk79-b-3p8gr4o!fw#a_x4deht3'

SERVER_EMAIL = ""
CUSTOMER_EMAIL = ""
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = "[Kashgar project] "

APPEND_SLASH = True

AUTH_PROFILE_MODULE = 'web.UserProfile'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    "/home/ionut/work/kashgar/templates",
    "/home/ionut/work/kashgar/templates/web"
)

INSTALLED_APPS = (
    'web',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
)
