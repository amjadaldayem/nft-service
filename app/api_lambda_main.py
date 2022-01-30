# Entrypoint for API Lambda
from mangum import Mangum

from app.web.api import app

handler = Mangum(app=app)