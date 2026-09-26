"""
Django settings for TechFlow.

TechFlow is a lightweight operational visibility system for the
Technology department. Configuration is environment-driven so the same
code runs locally and inside Docker Compose.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load .env files (optional; real environment variables win in Docker Compose).
# backend/.env (closest to the code) overrides the repository-root .env.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env", override=True)

# --- Security -------------------------------------------------------------
SECRET_KEY = os.environ.get("TECHFLOW_SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = os.environ.get("TECHFLOW_DEBUG", "1") == "1"

# Comma-separated via TECHFLOW_ALLOWED_HOSTS. In DEBUG, "*" is kept for
# convenience; in production the explicit list is enforced (fail safe:
# without the env var, localhost only).
_allowed_hosts = [
    h.strip()
    for h in os.environ.get("TECHFLOW_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]
ALLOWED_HOSTS = ["*"] if DEBUG else (_allowed_hosts or ["localhost", "127.0.0.1"])

# --- Applications ---------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "drf_spectacular",
    # Serves the Swagger UI assets locally (no CDN needed).
    "drf_spectacular_sidecar",
    # TechFlow apps
    "core",
    "organizations",
    "teams",
    "projects",
    "work",
    "blockers",
    "support",
    "capacity",
    "incoming",
    "audit_app",
    "dashboards",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "techflow.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # Serve the built frontend (if present) from Django.
            PROJECT_ROOT
            / "frontend"
            / "dist",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "techflow.wsgi.application"

# --- Database -------------------------------------------------------------
# Defaults point at a *local* PostgreSQL on the standard port 5432.
# Docker Compose overrides these (see docker-compose.yml / .env).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("TECHFLOW_DB_NAME", "techflow"),
        "USER": os.environ.get("TECHFLOW_DB_USER", "techflow"),
        "PASSWORD": os.environ.get("TECHFLOW_DB_PASSWORD", "techflow"),
        "HOST": os.environ.get("TECHFLOW_DB_HOST", "localhost"),
        "PORT": os.environ.get("TECHFLOW_DB_PORT", "5432"),
    }
}

# --- Authentication / REST framework --------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": ("rest_framework.pagination.PageNumberPagination"),
    "PAGE_SIZE": 100,
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# --- CSRF / origins ---------------------------------------------------------
# Django 5+ rejects POSTs whose Origin header is not trusted. The SPA dev
# server (Vite) proxies /api to Django but keeps its own origin, so it must be
# listed here. Extra origins can be added via TECHFLOW_CSRF_TRUSTED_ORIGINS
# (comma-separated), e.g. for production deployments.
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("TECHFLOW_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://localhost:5173", "http://127.0.0.1:5173"]

# --- Internationalization ---------------------------------------------------
LANGUAGE_CODE = "fa-IR"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# --- Static files -----------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = []
_dist_static = PROJECT_ROOT / "frontend" / "dist" / "assets"
if _dist_static.exists():
    STATICFILES_DIRS.append(_dist_static)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- API schema / Swagger (drf-spectacular) --------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "TechFlow API",
    "DESCRIPTION": "سامانه عملیات و پایش تیم فناوری — REST API (JSON, session auth)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Serve the Swagger UI assets from drf-spectacular-sidecar (local files)
    # instead of a CDN, so the docs work on restricted/offline networks.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
}

# --- TechFlow product settings ----------------------------------------------
# Transparent, configurable rules used by the "projects at risk" engine.
# These are operational signals, NOT subjective productivity scores.
RISK_DEADLINE_SOON_DAYS = int(os.environ.get("TECHFLOW_RISK_DEADLINE_SOON_DAYS", "14"))
RISK_STALE_UPDATE_DAYS = int(os.environ.get("TECHFLOW_RISK_STALE_UPDATE_DAYS", "14"))
RISK_OVERALLOCATION_THRESHOLD = int(
    os.environ.get("TECHFLOW_RISK_OVERALLOCATION_THRESHOLD", "110")
)
# A blocker is considered "aging" after this many days open.
BLOCKER_AGING_DAYS = int(os.environ.get("TECHFLOW_BLOCKER_AGING_DAYS", "7"))
# Priority changes / operational events shown as "recent" on dashboards.
RECENT_EVENTS_DAYS = int(os.environ.get("TECHFLOW_RECENT_EVENTS_DAYS", "14"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
