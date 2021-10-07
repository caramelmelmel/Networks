#===================== Importing FastAPI necessary packages =============
from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Request,
)

from src.routers import router


import base64
import binascii


#------------------ FastAPI variable ----------------------------------
app = FastAPI()

# ================= Routers inclusion from src directory ===============
app.include_router(router)
