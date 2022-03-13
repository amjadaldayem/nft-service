import os

import sentry_sdk
from sentry_sdk import set_tag

from app.settings import (
    ENV_TEST,
    ENV_LOCAL
)


def sentry_error_notify(e, metadata):
    with sentry_sdk.push_scope() as scope:
        scope.set_extra("metadata", metadata)
        sentry_sdk.capture_exception(e)


def initialize():
    from app import settings
    from app.utils import setup_logging
    from app.utils import setup_error_handler
    setup_logging(
        settings.DEBUG,
        envs_with_console_logging={settings.ENV_LOCAL, settings.ENV_TEST}
    )
    if settings.DEPLOYMENT_ENV not in (ENV_LOCAL, ENV_TEST):
        sentry_sdk.init(
            dsn=settings.SENTRY_IO_DSN,
            traces_sample_rate=settings.SENTRY_IO_TRACE_SAMPLERATE,
            debug=settings.SENTRY_IO_DEBUG,
            with_locals=settings.SENTRY_IO_WITH_LOCALS,
            max_breadcrumbs=settings.SENTRY_IO_MAX_BREADCRUMBS,
            request_bodies=settings.SENTRY_IO_CAPTURE_REQUEST_BODIES,
            environment=settings.DEPLOYMENT_ENV,
            default_integrations=True
        )
        set_tag("app_label", os.getenv('SENTRY_IO_APP_TAG', "unnamed"))
        setup_error_handler(sentry_error_notify)
