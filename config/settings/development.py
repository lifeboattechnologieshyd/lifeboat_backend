# ruff: noqa

from config.settings.common import *  # noqa : F403

############################
#       SILK SETTINGS      #
############################
ENABLE_SILK = True if os.environ.get("ENABLE_SILK", "False") == "True" else False

SILKY_PYTHON_PROFILER = True
SILKY_INTERCEPT_PERCENT = 100
SILKY_META = True

if ENABLE_SILK:
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]


FRONTEND_URL = "http://127.0.0.1"
ISHVAA_EMAIL_ID = 'ics_live_25I1njmlVD0OGiaL9orr4RxvTrgIO-JsR6HSRzkGcFY'