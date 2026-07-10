"""
Impostazioni Django per il progetto Ticket Reservation API.

Questo file è volutamente semplice e ben commentato, per essere facile da
seguire in un progetto universitario / da portfolio. Le configurazioni che
tipicamente cambiano tra un ambiente e l'altro (secret key, flag di debug,
host consentiti) vengono lette da variabili d'ambiente con valori
predefiniti sensati per lo sviluppo locale, così lo stesso identico codice
può essere distribuito su una piattaforma di hosting senza modifiche.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# ATTENZIONE SICUREZZA: mantieni segreta la secret key usata in produzione!
# Viene fornito un valore predefinito in modo che il progetto funzioni da
# subito in locale/demo. Imposta una vera variabile d'ambiente
# DJANGO_SECRET_KEY in produzione. Se manca e DEBUG è disattivato, viene
# emesso un warning ben visibile nei log invece di fallire silenziosamente
# con una chiave insicura (ISS-008) - un crash immediato qui romperebbe
# però l'uso locale/demo a configurazione zero descritto nel README, quindi
# si è scelto un avviso visibile piuttosto che un errore bloccante.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# ISS-008: il default era True, il che rendeva ALLOWED_HOSTS=["*"] e
# mostrava pagine di errore con stack trace/impostazioni a chiunque
# dimenticasse di impostare DJANGO_DEBUG in un deployment reale. Ora il
# default è False (comportamento sicuro "di serie"); per lo sviluppo
# locale imposta DJANGO_DEBUG=True nell'ambiente, oppure lascia pure il
# default: ALLOWED_HOSTS include comunque "localhost"/"127.0.0.1" più sotto,
# quindi `python manage.py runserver` funziona normalmente anche così.
DEBUG = env_bool("DJANGO_DEBUG", default=False)

if not SECRET_KEY:
    SECRET_KEY = "django-insecure-demo-key-for-local-development-only-change-me"
    if not DEBUG:
        import warnings

        warnings.warn(
            "DJANGO_SECRET_KEY non impostata e DEBUG=False: si sta usando una "
            "chiave di sviluppo insicura. Imposta una vera variabile "
            "d'ambiente DJANGO_SECRET_KEY prima di un deployment reale.",
            RuntimeWarning,
        )

# Elenco di host separati da virgola, es. "myapp.onrender.com,localhost"
_allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(",") if h.strip()] or [
    "localhost",
    "127.0.0.1",
]
# Consenti qualsiasi host quando DEBUG è attivo, così il progetto è facile
# da eseguire in locale / in un ambiente di valutazione sandbox senza
# configurazioni aggiuntive.
if DEBUG:
    ALLOWED_HOSTS = ["*"]

# Richiesto da Django quando l'app è dietro un proxy sulla maggior parte
# degli host PaaS (Render, Railway, ecc.), affinché i controlli CSRF
# accettino l'origine HTTPS pubblica.
_csrf_origins = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]


# Definizione dell'applicazione

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Librerie di terze parti
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    # App locali
    "accounts",
    "events",
    "reservations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# SQLite viene usato sia per lo sviluppo locale sia per il deploy demo, e
# il file db.sqlite3 già popolato è incluso nel repository. Se in futuro
# servisse un deployment in stile DATABASE_URL, questa è l'unica sezione
# da modificare.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Modello utente personalizzato (vedi app accounts)
AUTH_USER_MODEL = "accounts.CustomUser"


# Validazione della password
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internazionalizzazione
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# File statici (CSS, JavaScript, immagini) - serviti tramite WhiteNoise in produzione
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "core.storage.LenientManifestStaticFilesStorage",
    },
}

# Con DEBUG=False come nuovo default (ISS-008), il meccanismo automatico di
# staticfiles di Django (attivo solo con DEBUG=True) non servirebbe più i
# file statici in locale. WHITENOISE_USE_FINDERS permette a WhiteNoise di
# servirli comunque direttamente dagli static finder (es. il CSS
# dell'admin) senza dover prima eseguire collectstatic - utile in
# locale/demo; in produzione build.sh esegue comunque collectstatic, quindi
# lo storage compresso con manifest sopra resta pienamente utilizzato.
WHITENOISE_USE_FINDERS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    # Reso questo il backend di default: ReservationViewSet dichiara
    # filterset_fields ma non imposta un proprio filter_backends, quindi
    # senza questa entry i parametri ?status= e ?event= venivano ignorati
    # silenziosamente (ISS-001). EventViewSet imposta comunque i propri
    # filter_backends esplicitamente, quindi non è influenzato da questa
    # impostazione globale.
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# CORS: completamente aperto per questo progetto demo, così il client di
# test HTML incluso (aperto come file statico/locale o ospitato altrove)
# può chiamare l'API da qualsiasi origine. In un vero deployment di
# produzione, limita questa impostazione a origini conosciute.
CORS_ALLOW_ALL_ORIGINS = True

# Permette alla browsable API / admin di mostrare link HTTPS corretti
# quando l'app è distribuita dietro un reverse proxy che termina il TLS
# (Render, Railway, ecc.)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Protezioni valide solo se il sito è davvero servito in HTTPS. Nota: NON
# sono agganciate a DEBUG=False, perché da quando DEBUG è diventato False
# di default (ISS-008) "DEBUG=False" non implica più "sicuramente in
# produzione dietro HTTPS" - vale anche per un normale test locale in
# HTTP semplice, dove forzare SECURE_SSL_REDIRECT causerebbe un redirect
# 301 verso un HTTPS che in locale non esiste. Vanno quindi attivate
# esplicitamente solo dove il sito è realmente in HTTPS (render.yaml lo
# fa impostando DJANGO_USE_HTTPS=True).
if env_bool("DJANGO_USE_HTTPS", default=False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
