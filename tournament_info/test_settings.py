"""Isolated test settings; never connect to the configured MySQL database or S3.

Run with: python manage.py test --settings=tournament_info.test_settings
SQLite does not verify MySQL locking or conditional-constraint behavior.
"""

from .settings import *  # noqa: F403

SECRET_KEY = "isolated-tests-only-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
