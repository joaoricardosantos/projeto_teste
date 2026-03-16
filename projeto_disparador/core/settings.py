import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-default-key")

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

APPEND_SLASH = False

INSTALLED_APPS =[
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE =[
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES =[
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors":[
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "condo_db"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS =[
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "core.User"

EXTERNAL_MESSAGING_API_URL = os.environ.get("EXTERNAL_MESSAGING_API_URL", "")
EXTERNAL_MESSAGING_API_KEY = os.environ.get("EXTERNAL_MESSAGING_API_KEY", "")

# Configurações de integração com Superlógica
SUPERLOGICA_BASE_URL = os.environ.get(
    "SUPERLOGICA_BASE_URL", "https://api.superlogica.net/v2/condor"
)
SUPERLOGICA_APP_TOKEN    = os.environ.get("SUPERLOGICA_APP_TOKEN",    "")
SUPERLOGICA_ACCESS_TOKEN = os.environ.get("SUPERLOGICA_ACCESS_TOKEN", "")
SUPERLOGICA_MAX_ID       = int(os.environ.get("SUPERLOGICA_MAX_ID",   "100"))
 
# Evolution API (WhatsApp)
EVOLUTION_BASE_URL = os.environ.get("EVOLUTION_BASE_URL", "http://localhost:8080")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "minha-instancia")
EVOLUTION_API_KEY  = os.environ.get("EVOLUTION_API_KEY", "")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@seudominio.com.br")
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST          = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT          = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_USE_TLS       = os.environ.get("EMAIL_USE_TLS", "False") == "True"
EMAIL_USE_SSL       = os.environ.get("EMAIL_USE_SSL", "False") == "True"
EMAIL_HOST_USER     = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
