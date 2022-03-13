import os

import uvicorn

from app import settings  # noqa
from app.web.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('WEB_SERVER_PORT', '9000')), debug=True, access_log=False)
