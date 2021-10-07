from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

import os
import motor.motor_asyncio

# ================= Creating necessary variables ========================
#------------------ Token, authentication variables ---------------------



#----------------- Database variables (MongoDB) --------------------------
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["DB_URL"])
db = client.myTestDB
print("connected to mongodb")