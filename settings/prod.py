import json

from .base import *

DEFAULT_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


DATABASES = (
  json.loads(os.environ["APP_DATABASES"])
  if "APP_DATABASES" in os.environ
  else DEFAULT_DATABASES
)