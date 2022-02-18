import sentry_sdk


def sentry_error_notify(e, metadata):
    sentry_sdk.capture_exception(e, extra=metadata)


def initialize():
    from app import settings
    from app.utils import setup_logging
    setup_logging(settings.DEBUG)
    integrations = []
    sentry_sdk.init(
        dsn=settings.SENTRY_IO_DSN,
        integrations=integrations,
        traces_sample_rate=settings.SENTRY_IO_TRACE_SAMPLERATE,
        debug=settings.SENTRY_IO_DEBUG,
        with_locals=settings.SENTRY_IO_WITH_LOCALS,
        max_breadcrumbs=settings.SENTRY_IO_MAX_BREADCRUMBS,
        request_bodies=settings.SENTRY_IO_CAPTURE_REQUEST_BODIES,
        environment=settings.DEPLOYMENT_ENV
    )
    if settings.DEPLOYMENT_ENV not in ('local', 'test'):
        from app.utils import setup_error_handler
        setup_error_handler(sentry_error_notify)
