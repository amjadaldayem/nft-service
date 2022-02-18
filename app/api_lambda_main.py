# Entrypoint for API Lambda

from mangum import Mangum

from app.web.api import app
from .main import initialize

initialize(is_lambda=True)

handler = Mangum(app=app)
