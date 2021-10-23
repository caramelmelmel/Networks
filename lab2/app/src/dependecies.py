from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from .settings import db

from datetime import datetime, timedelta
from typing import Optional



async def get_user(id: str):
    if (user := await db["users"].find_one({"_id": id})) is not None:
        return user




