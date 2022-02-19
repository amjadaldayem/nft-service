import uvicorn
from app.web.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True, access_log=False)
